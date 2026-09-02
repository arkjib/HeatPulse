"""
feature_engineering.py
-----------------------
Builds the ML feature matrix from a historical thermal dataset (pandas DataFrame).

LEAKAGE RULE: All lag and rolling features for row i are computed using only
rows 0..i-1. The pd.shift() and .rolling() APIs enforce this automatically
because shift(k) moves values forward k steps (row i gets value from row i-k).

NO FUTURE INFORMATION enters any feature used to predict a target at horizon h.
"""
import numpy as np
import pandas as pd
from typing import List, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
LAG_HOURS = [1, 3, 6, 12, 24]
ROLL_WINDOWS = [6, 12, 24]
WBGT_STRESS_THRESHOLD = 28.0   # °C — ISO 7243 "moderate" heat stress boundary
UTCI_STRESS_THRESHOLD = 32.0   # °C — UTCI "strong heat stress" lower bound
FORECAST_HORIZONS = [24, 48, 72, 96, 120]

# Variables used as raw features
MET_FEATURES = [
    "temp_c", "rh_pct", "wind_ms", "pressure_hpa",
    "ghi_wm2", "direct_rad", "diffuse_rad", "dni",
]
THERMAL_FEATURES = ["heat_index_c", "wbgt_c", "utci_c", "mrt_c"]
ALL_BASE_FEATURES = MET_FEATURES + THERMAL_FEATURES


def build_features(df: pd.DataFrame, lat: float, lon: float) -> pd.DataFrame:
    """
    Given a chronologically-ordered DataFrame (one row per hour), return an
    enriched DataFrame containing:
      - temporal features
      - lag features (past observations)
      - rolling mean/max features
      - consecutive-stress counters
      - forecast horizon targets (WBGT, UTCI, HI shifted forward)

    Parameters
    ----------
    df  : DataFrame from dataset_builder — must have 'timestamp' as DatetimeTZAware column
    lat : location latitude (stored as metadata, not used as a feature here)
    lon : location longitude

    Returns
    -------
    DataFrame with feature columns + target columns (columns prefixed 'target_').
    Rows with insufficient history for lags/rolling are NaN — the caller must dropna.
    """
    df = df.copy().reset_index(drop=True)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df.sort_values("timestamp").reset_index(drop=True)

    # -----------------------------------------------------------------------
    # 1. Temporal features
    # -----------------------------------------------------------------------
    df["hour"] = df["timestamp"].dt.hour
    df["day_of_year"] = df["timestamp"].dt.day_of_year
    df["month"] = df["timestamp"].dt.month
    # Simple daytime proxy: hour 6–18 UTC (approximate; exact solar position handled by STEP 3)
    df["is_daytime"] = ((df["hour"] >= 6) & (df["hour"] <= 18)).astype(int)
    # Cyclical encoding of hour and day_of_year to preserve periodicity
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
    df["doy_sin"] = np.sin(2 * np.pi * df["day_of_year"] / 365)
    df["doy_cos"] = np.cos(2 * np.pi * df["day_of_year"] / 365)

    # -----------------------------------------------------------------------
    # 2. Lag features — strictly backward-looking
    # -----------------------------------------------------------------------
    for col in ALL_BASE_FEATURES:
        if col not in df.columns:
            continue
        for lag in LAG_HOURS:
            df[f"{col}_lag{lag}h"] = df[col].shift(lag)

    # -----------------------------------------------------------------------
    # 3. Rolling features — min_periods avoids silent NaN propagation
    # -----------------------------------------------------------------------
    for col in ["wbgt_c", "utci_c", "heat_index_c", "temp_c"]:
        if col not in df.columns:
            continue
        for window in ROLL_WINDOWS:
            df[f"{col}_roll_mean_{window}h"] = (
                df[col].shift(1).rolling(window, min_periods=window // 2).mean()
            )
            df[f"{col}_roll_max_{window}h"] = (
                df[col].shift(1).rolling(window, min_periods=window // 2).max()
            )

    # -----------------------------------------------------------------------
    # 4. Consecutive stress counters (hours above threshold)
    # -----------------------------------------------------------------------
    if "wbgt_c" in df.columns:
        above_wbgt = (df["wbgt_c"].shift(1) >= WBGT_STRESS_THRESHOLD).fillna(False)
        df["hours_wbgt_above_28"] = _consecutive_true(above_wbgt)

    if "utci_c" in df.columns:
        above_utci = (df["utci_c"].shift(1) >= UTCI_STRESS_THRESHOLD).fillna(False)
        df["hours_utci_above_32"] = _consecutive_true(above_utci)

    # -----------------------------------------------------------------------
    # 5. Forecast horizon targets (shift forward = future values)
    # -----------------------------------------------------------------------
    target_cols = {}
    for h in FORECAST_HORIZONS:
        if "wbgt_c" in df.columns:
            target_cols[f"target_wbgt_h{h}"] = df["wbgt_c"].shift(-h)
        if "utci_c" in df.columns:
            target_cols[f"target_utci_h{h}"] = df["utci_c"].shift(-h)
        if "heat_index_c" in df.columns:
            target_cols[f"target_hi_h{h}"] = df["heat_index_c"].shift(-h)

    if target_cols:
        df = pd.concat([df, pd.DataFrame(target_cols, index=df.index)], axis=1)

    return df


def _consecutive_true(series: pd.Series) -> pd.Series:
    """
    For each position i, return the number of consecutive True values
    ending at i-1 (i.e., strictly backward-looking consecutive counter).
    """
    result = np.zeros(len(series), dtype=float)
    count = 0
    arr = series.values
    for i in range(len(arr)):
        if arr[i]:
            count += 1
        else:
            count = 0
        result[i] = count
    return pd.Series(result, index=series.index)


def get_feature_columns(df: pd.DataFrame) -> List[str]:
    """Return the list of feature column names (excludes targets and metadata)."""
    exclude = {"timestamp", "hi_status", "wbgt_status", "utci_status"}
    target_prefix = "target_"
    return [
        c for c in df.columns
        if c not in exclude and not c.startswith(target_prefix)
        and not c.endswith("_status")
    ]


def chronological_split(
    df: pd.DataFrame,
    train_frac: float = 0.70,
    val_frac: float = 0.15,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split chronologically into train / validation / test.
    NO shuffling. The three sets are non-overlapping and ordered by time.
    """
    n = len(df)
    n_train = int(n * train_frac)
    n_val = int(n * val_frac)
    train = df.iloc[:n_train].copy()
    val = df.iloc[n_train : n_train + n_val].copy()
    test = df.iloc[n_train + n_val :].copy()
    return train, val, test
