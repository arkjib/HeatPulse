"""
forecasting.py  (app/models/forecasting.py)
--------------------------------------------
Service layer that:
  1. Loads approved trained models from the registry.
  2. Accepts forecast weather (WeatherForecast) + location metadata.
  3. Computes STEP 3 physical thermal indices on each forecast hour.
  4. Builds lag/rolling features from the forecast sequence (within-forecast
     context window — see LEAKAGE NOTE).
  5. Calls separate ML models (WBGT, UTCI, HI) for each horizon.
  6. Returns predictions including both ML and physical (STEP 3) values
     so callers can compare the two.

LEAKAGE NOTE:
  For live inference, the forecast sequence provides future weather but NOT
  future observed thermal indices. Lag/rolling features for hour i are built
  from hours 0..i-1 in the same forecast window. This is consistent with
  what was available at training time for the same lag offsets.
  Target horizons correspond to absolute offsets from the first forecast hour.

ML PURPOSE NOTE:
  The ML models are NOT meant to reproduce the deterministic STEP 3 equations.
  They learn local temporal behavior — persistence, heat accumulation, diurnal
  patterns — that the purely physics-driven STEP 3 forecast cannot capture.
  Both ML predictions and physical predictions are returned so the API consumer
  can evaluate which performs better for their use case.
"""
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Registry path relative to this file
_REGISTRY_ROOT = Path(__file__).parent.parent.parent / "training"


def _load_registry():
    """Lazy import to avoid circular dependencies at module load time."""
    import sys
    sys.path.insert(0, str(_REGISTRY_ROOT.parent))
    from training.model_registry import (
        load_model, get_model_status, get_all_metadata,
        STATUS_READY, STATUS_NOT_TRAINED, STATUS_ERROR,
    )
    return load_model, get_model_status, get_all_metadata, STATUS_READY, STATUS_NOT_TRAINED, STATUS_ERROR


def _load_feature_engineering():
    import sys
    sys.path.insert(0, str(_REGISTRY_ROOT.parent))
    from training.feature_engineering import (
        build_features, get_feature_columns, FORECAST_HORIZONS,
    )
    return build_features, get_feature_columns, FORECAST_HORIZONS


TARGETS = ["wbgt", "utci", "hi"]
HORIZONS = [24, 48, 72, 96, 120]


def _thermal_stress_score(
    wbgt: Optional[float],
    utci: Optional[float],
    hi: Optional[float],
) -> Optional[float]:
    """
    Normalized composite thermal stress score 0–1.
    Uses available indices; returns None if all are unavailable.
    Reference ranges: WBGT 0–40°C, UTCI -50–50°C, HI 27–55°C.
    """
    scores = []
    if wbgt is not None:
        scores.append(min(max((wbgt - 0) / 40.0, 0.0), 1.0))
    if utci is not None:
        scores.append(min(max((utci - (-50)) / 100.0, 0.0), 1.0))
    if hi is not None:
        scores.append(min(max((hi - 27) / 28.0, 0.0), 1.0))
    if not scores:
        return None
    return round(sum(scores) / len(scores), 3)


class ForecastingService:
    """
    Manages model loading, feature engineering, and thermal stress prediction.
    Each (target, horizon) pair has its own independently trained estimator.
    """

    def __init__(self):
        self._models: Dict[str, Any] = {}   # key: "wbgt_h24", "utci_h48", etc.
        self._metadata: Dict[str, Any] = {}
        self._status: str = "MODEL_NOT_TRAINED"
        self._feature_cols: Optional[List[str]] = None

    def load(self) -> str:
        """
        Attempt to load all approved models from the registry.
        Returns the model status string.
        """
        try:
            load_model, get_model_status, get_all_metadata, S_READY, S_NOT, S_ERR = _load_registry()
            status = get_model_status()
            self._status = status

            if status != S_READY:
                logger.info(f"Model registry status: {status}")
                return status

            all_meta = get_all_metadata()
            loaded = 0
            for target in TARGETS:
                for h in HORIZONS:
                    key = f"{target}_h{h}"
                    try:
                        model, meta = load_model(target, h)
                        self._models[key] = model
                        self._metadata[key] = meta
                        loaded += 1
                        # Cache feature columns from first successful load
                        if self._feature_cols is None and "feature_columns" in meta:
                            self._feature_cols = meta["feature_columns"]
                    except FileNotFoundError:
                        pass  # Not all (target, horizon) combinations may exist

            logger.info(f"Loaded {loaded} trained model artifacts.")
            return status

        except Exception as e:
            logger.error(f"Model loading failed: {e}")
            self._status = "MODEL_ERROR"
            return self._status

    def predict(
        self,
        forecast_hours: List[Dict[str, Any]],
        lat: float,
        lon: float,
    ) -> List[Dict[str, Any]]:
        """
        Generate thermal stress predictions for each forecast hour.

        Parameters
        ----------
        forecast_hours : list of dicts, each with meteorological + thermal fields
                         (already computed by the API layer via STEP 3)
        lat, lon       : location

        Returns
        -------
        List of prediction dicts keyed by horizon_hours.
        """
        if self._status != "MODEL_READY" or not self._models:
            return []

        build_features, get_feature_columns, _ = _load_feature_engineering()

        # Build a DataFrame from the forecast window
        df = pd.DataFrame(forecast_hours)
        if "timestamp" not in df.columns or df.empty:
            return []

        df["latitude"] = lat
        df["longitude"] = lon

        # Build features (lag/rolling within the forecast window)
        try:
            fe_df = build_features(df, lat, lon)
        except Exception as e:
            logger.error(f"Feature engineering failed: {e}")
            return []

        feature_cols = self._feature_cols or get_feature_columns(fe_df)
        # Fill missing feature cols with NaN rather than crashing
        for col in feature_cols:
            if col not in fe_df.columns:
                fe_df[col] = np.nan

        results = []
        n = len(fe_df)

        for h in HORIZONS:
            # The prediction for horizon h corresponds to the row at offset h
            # from the start of the forecast window.
            if h >= n:
                continue
            target_row = fe_df.iloc[h]
            target_ts = target_row.get("timestamp")
            X = fe_df.iloc[[h]][feature_cols].values

            preds = {}
            for target in TARGETS:
                key = f"{target}_h{h}"
                if key in self._models:
                    try:
                        val = float(self._models[key].predict(X)[0])
                        preds[target] = round(val, 2)
                    except Exception:
                        preds[target] = None
                else:
                    preds[target] = None

            # Physical values (STEP 3 applied to forecast weather at that hour)
            phys_row = forecast_hours[h] if h < len(forecast_hours) else {}

            results.append({
                "timestamp": target_ts,
                "horizon_hours": h,
                "wbgt_c": preds.get("wbgt"),
                "utci_c": preds.get("utci"),
                "heat_index_c": preds.get("hi"),
                "wbgt_physical_c": phys_row.get("wbgt_c"),
                "utci_physical_c": phys_row.get("utci_c"),
                "heat_index_physical_c": phys_row.get("heat_index_c"),
                "thermal_stress_score": _thermal_stress_score(
                    preds.get("wbgt"), preds.get("utci"), preds.get("hi")
                ),
            })

        return results
