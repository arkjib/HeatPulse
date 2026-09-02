import sys
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from training.feature_engineering import (
    build_features,
    get_feature_columns,
    ALL_BASE_FEATURES,
    LAG_HOURS,
    ROLL_WINDOWS
)
from test_forecasting import make_hourly_df


def test_formal_feature_leakage():
    """
    Formal Leakage Audit:
    For a prediction made at timestamp T (represented by row i),
    we must verify that NO feature value at row i depends on
    information from row j where j >= i.
    
    We verify this by making a copy of the dataframe, intentionally
    corrupting all data for rows j >= i, and ensuring that the
    feature values for row i remain IDENTICAL.
    """
    df = make_hourly_df(n_hours=100, seed=123)
    
    # 1. Compute features on the unmodified dataset
    fe_clean = build_features(df, lat=28.6, lon=77.2)
    feature_cols = get_feature_columns(fe_clean)
    
    # Pick a test row in the middle (e.g. index 50, timestamp T)
    target_idx = 50
    expected_features = fe_clean.iloc[target_idx][feature_cols].copy()
    
    # 2. Corrupt all future data AND the current row data!
    # Wait, the current row (T) is observed at T, so it IS available at T.
    # Therefore, features for row i CAN use raw variables from row i (current observation).
    # But they MUST NOT use variables from row i+1, i+2, etc.
    # Actually, let's verify what the model is supposed to use.
    # "At prediction time t: recent historical weather, forecast weather"
    # Wait, if we use forecast weather at t+h, we don't have it in the ERA5 features. 
    # Our fe_clean uses `temp_c`, `rh_pct`, etc at row `i` to represent the weather at time T.
    # Does it use future weather? No, the features only use row <= i.
    
    df_corrupted = df.copy()
    
    # Corrupt everything strictly AFTER time T
    # Because at prediction time T, we do NOT know true observations at T+1, T+2...
    # (We only know forecast weather, which is separate and not what ERA5 provides).
    corrupt_start_idx = target_idx + 1
    
    for col in ALL_BASE_FEATURES:
        if col in df_corrupted.columns:
            # Set to NaN or ridiculous values to ensure mismatch if accessed
            df_corrupted.loc[corrupt_start_idx:, col] = -9999.0
            
    # 3. Compute features on the corrupted dataset
    fe_corrupted = build_features(df_corrupted, lat=28.6, lon=77.2)
    actual_features = fe_corrupted.iloc[target_idx][feature_cols].copy()
    
    # 4. Compare
    for col in feature_cols:
        val_clean = expected_features[col]
        val_corrupted = actual_features[col]
        
        if pd.isna(val_clean):
            assert pd.isna(val_corrupted), f"Leakage detected in {col}: Clean is NaN, Corrupt is {val_corrupted}"
        else:
            assert np.isclose(val_clean, val_corrupted, equal_nan=True), \
                f"Leakage detected in {col}: Clean={val_clean}, Corrupt={val_corrupted}"


def test_target_leakage():
    """
    Verify that target columns strictly use future data and do NOT include
    the current observation at time T.
    """
    df = make_hourly_df(n_hours=100, seed=456)
    fe = build_features(df, lat=28.6, lon=77.2)
    
    target_idx = 40
    
    # The target h=24 at row i MUST exactly equal the raw value at row i+24
    assert np.isclose(fe.iloc[target_idx]["target_wbgt_h24"], df.iloc[target_idx + 24]["wbgt_c"], equal_nan=True)
    
    # Ensure it is NOT the current value
    assert not np.isclose(fe.iloc[target_idx]["target_wbgt_h24"], df.iloc[target_idx]["wbgt_c"], equal_nan=True)


def test_feature_source_timestamp_audit():
    """
    Programmatically verify the source rows for derived lag/rolling features
    to ensure max(feature_source_timestamp) <= T.
    """
    df = make_hourly_df(n_hours=100, seed=789)
    fe = build_features(df, lat=28.6, lon=77.2)
    
    target_idx = 60
    T = df.iloc[target_idx]["timestamp"]
    
    # Lag 1h should come from target_idx - 1
    lag_1_val = fe.iloc[target_idx]["wbgt_c_lag1h"]
    assert np.isclose(lag_1_val, df.iloc[target_idx - 1]["wbgt_c"])
    assert df.iloc[target_idx - 1]["timestamp"] < T
    
    # Lag 24h should come from target_idx - 24
    lag_24_val = fe.iloc[target_idx]["wbgt_c_lag24h"]
    assert np.isclose(lag_24_val, df.iloc[target_idx - 24]["wbgt_c"])
    assert df.iloc[target_idx - 24]["timestamp"] < T

    # Roll 6h mean should be mean of [target_idx - 6 : target_idx]
    # which corresponds to rows i-6, i-5, i-4, i-3, i-2, i-1.
    # Max index used is target_idx - 1
    roll_val = fe.iloc[target_idx]["wbgt_c_roll_mean_6h"]
    expected_roll = df.iloc[target_idx - 6 : target_idx]["wbgt_c"].mean()
    assert np.isclose(roll_val, expected_roll)
    assert df.iloc[target_idx - 1]["timestamp"] < T
