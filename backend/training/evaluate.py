import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

sys.path.insert(0, str(Path(__file__).parent.parent))

from training.feature_engineering import (
    FORECAST_HORIZONS,
    build_features,
    chronological_split,
    get_feature_columns,
)
from training.model_registry import load_model, _load_all_metadata, _write_all_metadata


TARGETS = {
    "wbgt": "wbgt_c",
    "utci": "utci_c",
    "hi": "heat_index_c",
}

def _metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    mask = ~(np.isnan(y_true) | np.isnan(y_pred))
    if mask.sum() < 2:
        return {"MAE": None, "RMSE": None, "R2": None, "n": 0}
    y_t, y_p = y_true[mask], y_pred[mask]
    mae = mean_absolute_error(y_t, y_p)
    rmse = mean_squared_error(y_t, y_p) ** 0.5
    r2 = r2_score(y_t, y_p)
    
    # Statistical sanity checks
    vmin = float(y_p.min())
    vmax = float(y_p.max())
    vmean = float(y_p.mean())
    tmin = float(y_t.min())
    tmax = float(y_t.max())
    tmean = float(y_t.mean())
    correlation = float(np.corrcoef(y_t, y_p)[0, 1]) if np.std(y_p) > 0 and np.std(y_t) > 0 else 0.0
    
    residuals = y_t - y_p
    res_mean = float(residuals.mean())
    res_std = float(residuals.std())

    return {
        "MAE": round(mae, 3), 
        "RMSE": round(rmse, 3), 
        "R2": round(r2, 4), 
        "n": int(mask.sum()),
        "pred_min": round(vmin, 3),
        "pred_max": round(vmax, 3),
        "pred_mean": round(vmean, 3),
        "actual_min": round(tmin, 3),
        "actual_max": round(tmax, 3),
        "actual_mean": round(tmean, 3),
        "correlation": round(correlation, 3),
        "res_mean": round(res_mean, 3),
        "res_std": round(res_std, 3)
    }


def evaluate(dataset_path: str) -> None:
    df = pd.read_parquet(dataset_path)
    lat = float(df["latitude"].iloc[0])
    lon = float(df["longitude"].iloc[0])

    fe_df = build_features(df, lat, lon)
    feature_cols = get_feature_columns(fe_df)
    fe_df = fe_df.dropna(subset=feature_cols).reset_index(drop=True)

    _, _, test = chronological_split(fe_df)
    
    # Very important: make sure we use exactly the feature columns required by the model
    
    print("\n" + "=" * 100)
    print("SIH26083 THERMAL STRESS FORECAST — EVALUATION REPORT")
    print("=" * 100)
    print(f"Test set: {test['timestamp'].iloc[0]} -> {test['timestamp'].iloc[-1]}")
    print(f"Test rows (Total): {len(test)}")
    print("PHYSICS_FORECAST_BASELINE: NOT_AVAILABLE (No historical NWP forecasts)")
    print()

    print(f"{'Target':<6} | {'Horizon':>7} | {'Model':>12} | {'Test RMSE':>9} | {'Pers RMSE':>9} | {'Improve':>8} | {'Test MAE':>8} | {'Test R²':>7} | {'Samples':>7}")
    print("-" * 100)

    # We will update metadata registry at the end
    all_meta = _load_all_metadata()
    results = []

    for target_key, raw_col in TARGETS.items():
        for h in FORECAST_HORIZONS:
            target_col = f"target_{target_key}_h{h}"
            if target_col not in test.columns:
                continue
            
            y_true = test[target_col].values.astype(float)

            # Persistence baseline
            if raw_col in test.columns:
                y_persist = test[raw_col].values.astype(float)
                persist_m = _metrics(y_true, y_persist)
            else:
                persist_m = {"RMSE": None, "n": 0}

            # ML model
            key = f"{target_key}_h{h}"
            try:
                model, meta = load_model(target_key, h)
                # Ensure we select exactly the features used during training
                X_cols = meta.get("feature_columns", feature_cols)
                X_test = test[X_cols].values
                y_ml = model.predict(X_test).astype(float)
                ml_m = _metrics(y_true, y_ml)
                model_used = meta.get("best_candidate", "unknown")
                
                # Check for physically suspicious predictions
                suspicious = []
                if target_key == "wbgt" and (ml_m["pred_max"] > 60.0 or ml_m["pred_min"] < -20.0):
                    suspicious.append("Suspicious WBGT limits")
                if target_key == "utci" and (ml_m["pred_max"] > 70.0 or ml_m["pred_min"] < -50.0):
                    suspicious.append("Suspicious UTCI limits")
                if target_key == "hi" and (ml_m["pred_max"] > 70.0 or ml_m["pred_min"] < -20.0):
                    suspicious.append("Suspicious HI limits")

                # Improvement
                p_rmse = persist_m.get("RMSE")
                ml_rmse = ml_m.get("RMSE")
                improve_pct = None
                if p_rmse and ml_rmse and p_rmse > 0:
                    improve_pct = (p_rmse - ml_rmse) / p_rmse * 100
                
                improve_str = f"{improve_pct:+.1f}%" if improve_pct is not None else "N/A"
                fmt = lambda v: f"{v:.3f}" if v is not None else "N/A"
                
                print(
                    f"{target_key:<6} | {h:>6}h | {model_used:>12} | {fmt(ml_rmse):>9} | {fmt(p_rmse):>9} | "
                    f"{improve_str:>8} | {fmt(ml_m.get('MAE')):>8} | {fmt(ml_m.get('R2')):>7} | {ml_m.get('n', 0):>7}"
                )
                
                if suspicious:
                    print(f"       WARNING: {', '.join(suspicious)}")
                    print(f"       [Min: {ml_m['pred_min']}, Max: {ml_m['pred_max']}, Mean: {ml_m['pred_mean']}] vs Actual [Min: {ml_m['actual_min']}, Max: {ml_m['actual_max']}, Mean: {ml_m['actual_mean']}]")

                # Statistical checks
                # print(f"       Corr: {ml_m['correlation']} | Res Mean: {ml_m['res_mean']} | Res Std: {ml_m['res_std']}")
                
                # Update metadata safely
                if key in all_meta:
                    all_meta[key]["test_metrics"] = {
                        "rmse": ml_rmse,
                        "mae": ml_m.get("MAE"),
                        "r2": ml_m.get("R2"),
                        "persist_rmse": p_rmse,
                        "improvement_over_persist_pct": round(improve_pct, 2) if improve_pct else None,
                        "samples": ml_m.get("n", 0),
                        "pred_min": ml_m["pred_min"],
                        "pred_max": ml_m["pred_max"],
                        "pred_mean": ml_m["pred_mean"],
                        "actual_min": ml_m["actual_min"],
                        "actual_max": ml_m["actual_max"],
                        "actual_mean": ml_m["actual_mean"],
                        "correlation": ml_m["correlation"],
                        "residual_mean": ml_m["res_mean"],
                        "residual_std": ml_m["res_std"]
                    }

            except Exception as e:
                print(f"{target_key:<6} | {h:>6}h | ERROR: {e}")

    # Write back the metadata
    _write_all_metadata(all_meta)
    print("\n" + "=" * 100)
    print("Test metrics safely saved to model_metadata.json (validation metrics preserved).")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, help="Path to parquet dataset")
    args = parser.parse_args()
    evaluate(args.dataset)


if __name__ == "__main__":
    main()
