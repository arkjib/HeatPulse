"""
train.py
--------
Trains separate ML models for each (target, horizon) combination.

Targets  : wbgt, utci, hi
Horizons : 24h, 48h, 72h, 96h, 120h  → 15 models total

Architecture:
  Historical weather (ERA5 via Open-Meteo)
        ↓
  Validated STEP 3 thermal engine (historical_thermal.py)
        ↓
  Feature engineering (lag / rolling / temporal)
        ↓
  Chronological split (no shuffling)
        ↓
  Candidates: LinearRegression, RandomForest, GradientBoosting
        ↓
  Best by val RMSE → saved via model_registry

The ML layer adds value over deterministic STEP 3 by learning local
temporal patterns, persistence effects, and forecast bias in the
historical record — not by re-implementing the physics.

Usage:
  cd backend
  python training/train.py --dataset training/data/thermal_history_28.61_77.23_*.parquet
"""
import argparse
import logging
import sys
import warnings
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).parent.parent))

from training.feature_engineering import (
    FORECAST_HORIZONS,
    build_features,
    chronological_split,
    get_feature_columns,
)
from training.model_registry import save_model, STATUS_NOT_TRAINED

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore", category=UserWarning)

RANDOM_SEED = 42  # Documented seed for reproducibility

TARGETS = {
    "wbgt": "wbgt_c",
    "utci": "utci_c",
    "hi": "heat_index_c",
}

CANDIDATES = {
    "ridge": Pipeline([
        ("scaler", StandardScaler()),
        ("model", Ridge(alpha=1.0, random_state=RANDOM_SEED)),
    ]),
    "rf": RandomForestRegressor(
        n_estimators=100,
        max_depth=12,
        min_samples_leaf=5,
        n_jobs=-1,
        random_state=RANDOM_SEED,
    ),
    "gbm": GradientBoostingRegressor(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=5,
        subsample=0.8,
        random_state=RANDOM_SEED,
    ),
}


def _rmse(y_true, y_pred):
    mask = ~(np.isnan(y_true) | np.isnan(y_pred))
    if mask.sum() < 2:
        return float("inf")
    return mean_squared_error(y_true[mask], y_pred[mask]) ** 0.5


def train(dataset_path: str) -> None:
    logger.info(f"Loading dataset: {dataset_path}")
    df = pd.read_parquet(dataset_path)
    lat = float(df["latitude"].iloc[0])
    lon = float(df["longitude"].iloc[0])

    logger.info("Building features...")
    fe_df = build_features(df, lat, lon)
    feature_cols = get_feature_columns(fe_df)

    # Drop rows that have NaN in any feature (lag/rolling warmup period)
    fe_df = fe_df.dropna(subset=feature_cols).reset_index(drop=True)

    train_df, val_df, test_df = chronological_split(fe_df)

    logger.info(
        f"Split sizes — Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}"
    )
    logger.info(
        f"Train period: {train_df['timestamp'].iloc[0]} → {train_df['timestamp'].iloc[-1]}"
    )
    logger.info(
        f"Val period:   {val_df['timestamp'].iloc[0]} → {val_df['timestamp'].iloc[-1]}"
    )
    logger.info(
        f"Test period:  {test_df['timestamp'].iloc[0]} → {test_df['timestamp'].iloc[-1]}"
    )

    X_train = train_df[feature_cols].values
    X_val = val_df[feature_cols].values

    summary_rows = []

    for target_key, raw_col in TARGETS.items():
        logger.info(f"\n{'='*60}")
        logger.info(f"Training target: {target_key.upper()}")

        for h in FORECAST_HORIZONS:
            target_col = f"target_{target_key}_h{h}"
            if target_col not in train_df.columns:
                logger.warning(f"Missing target column {target_col}, skipping.")
                continue

            y_train = train_df[target_col].values.astype(float)
            y_val = val_df[target_col].values.astype(float)

            # Only train on rows where target is not NaN
            train_mask = ~np.isnan(y_train)
            val_mask = ~np.isnan(y_val)

            if train_mask.sum() < 50:
                logger.warning(f"{target_col}: insufficient training rows ({train_mask.sum()}), skipping.")
                continue

            # --- Persistence baseline ---
            if raw_col in val_df.columns:
                y_persist = val_df[raw_col].values.astype(float)
                persist_rmse = _rmse(y_val[val_mask], y_persist[val_mask])
            else:
                persist_rmse = float("inf")

            # --- Train candidates ---
            best_name, best_model, best_rmse = None, None, float("inf")

            for cname, candidate in CANDIDATES.items():
                import copy
                m = copy.deepcopy(candidate)
                try:
                    m.fit(X_train[train_mask], y_train[train_mask])
                    y_pred_val = m.predict(X_val)
                    rmse = _rmse(y_val[val_mask], y_pred_val[val_mask])
                    logger.info(f"  {target_key} h={h}h {cname}: val RMSE={rmse:.3f}")
                    if rmse < best_rmse:
                        best_rmse = rmse
                        best_name = cname
                        best_model = m
                except Exception as e:
                    logger.warning(f"  {cname} failed: {e}")

            if best_model is None:
                logger.error(f"All candidates failed for {target_col}")
                continue

            # --- Save best model ---
            ml_vs_persist_pct = (
                (persist_rmse - best_rmse) / persist_rmse * 100
                if persist_rmse > 0 and persist_rmse != float("inf")
                else None
            )
            meta = {
                "feature_columns": feature_cols,
                "feature_count": len(feature_cols),
                "random_seed": RANDOM_SEED,
                "best_candidate": best_name,
                "val_rmse": round(best_rmse, 4),
                "persist_baseline_val_rmse": round(persist_rmse, 4) if persist_rmse != float("inf") else None,
                "ml_improvement_over_persist_pct": round(ml_vs_persist_pct, 2) if ml_vs_persist_pct is not None else None,
                "training_rows": int(train_mask.sum()),
                "data_period": {
                    "train_start": str(train_df["timestamp"].iloc[0]),
                    "train_end": str(train_df["timestamp"].iloc[-1]),
                    "val_start": str(val_df["timestamp"].iloc[0]),
                    "val_end": str(val_df["timestamp"].iloc[-1]),
                    "test_start": str(test_df["timestamp"].iloc[0]),
                    "test_end": str(test_df["timestamp"].iloc[-1]),
                },
            }
            save_model(best_model, target_key, h, meta)
            logger.info(
                f"  ✓ Saved: {target_key} h={h}h → {best_name} "
                f"(val RMSE={best_rmse:.3f}, persist RMSE={persist_rmse:.3f}, "
                f"improvement={ml_vs_persist_pct:+.1f}% vs persist)"
                if ml_vs_persist_pct is not None else
                f"  ✓ Saved: {target_key} h={h}h → {best_name} (val RMSE={best_rmse:.3f})"
            )
            summary_rows.append({
                "target": target_key,
                "horizon": h,
                "best_model": best_name,
                "val_rmse": round(best_rmse, 3),
                "persist_rmse": round(persist_rmse, 3) if persist_rmse != float("inf") else None,
                "improvement_pct": round(ml_vs_persist_pct, 1) if ml_vs_persist_pct is not None else None,
            })

    # Final summary table
    print("\n" + "=" * 70)
    print("TRAINING COMPLETE — VALIDATION SUMMARY")
    print("=" * 70)
    print(f"{'Target':>6} | {'Horizon':>8} | {'Best Model':>20} | {'Val RMSE':>9} | {'Persist RMSE':>13} | {'Improvement':>12}")
    print("-" * 80)
    for r in summary_rows:
        p = f"{r['persist_rmse']:.3f}" if r['persist_rmse'] else "N/A"
        imp = f"{r['improvement_pct']:+.1f}%" if r['improvement_pct'] is not None else "N/A"
        print(f"  {r['target']:>4} | h={r['horizon']:>5}h | {r['best_model']:>20} | {r['val_rmse']:>9.3f} | {p:>13} | {imp:>12}")

    print(f"\nAll models saved to: training/artifacts/")
    print("Run training/evaluate.py to get full test-set metrics.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    args = parser.parse_args()
    train(args.dataset)


if __name__ == "__main__":
    main()
