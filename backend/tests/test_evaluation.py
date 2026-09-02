import sys
from pathlib import Path
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from training.feature_engineering import build_features, get_feature_columns, chronological_split, FORECAST_HORIZONS
from training.model_registry import load_model

TARGETS = ["wbgt", "utci", "hi"]

def test_test_period_boundaries():
    dataset_path = "backend/training/data/thermal_history_10.25_76.25_grib.parquet"
    if not Path(dataset_path).exists():
        return # Skip if dataset doesn't exist
    
    df = pd.read_parquet(dataset_path)
    lat = float(df["latitude"].iloc[0])
    lon = float(df["longitude"].iloc[0])
    fe_df = build_features(df, lat, lon)
    
    feature_cols = get_feature_columns(fe_df)
    fe_df = fe_df.dropna(subset=feature_cols).reset_index(drop=True)

    train, val, test = chronological_split(fe_df)
    
    # Assert boundaries are strictly chronological
    assert train["timestamp"].iloc[-1] < val["timestamp"].iloc[0]
    assert val["timestamp"].iloc[-1] < test["timestamp"].iloc[0]

def test_no_nan_inf_predictions():
    dataset_path = "backend/training/data/thermal_history_10.25_76.25_grib.parquet"
    if not Path(dataset_path).exists():
        return
        
    df = pd.read_parquet(dataset_path)
    lat = float(df["latitude"].iloc[0])
    lon = float(df["longitude"].iloc[0])
    fe_df = build_features(df, lat, lon)
    feature_cols = get_feature_columns(fe_df)
    fe_df = fe_df.dropna(subset=feature_cols).reset_index(drop=True)

    _, _, test = chronological_split(fe_df)
    
    for target in TARGETS:
        for h in FORECAST_HORIZONS:
            model, meta = load_model(target, h)
            X_cols = meta.get("feature_columns", feature_cols)
            assert list(X_cols) == feature_cols, f"Feature ordering mismatch for {target} {h}h"
            
            X_test = test[X_cols].values
            y_pred = model.predict(X_test)
            
            # Assert no NaNs or Infs
            assert not np.isnan(y_pred).any()
            assert not np.isinf(y_pred).any()
            
            # Assert physical bounds
            assert y_pred.max() < 100.0, f"Unrealistically high prediction for {target} {h}h"
            assert y_pred.min() > -50.0, f"Unrealistically low prediction for {target} {h}h"
