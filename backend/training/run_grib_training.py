import xarray as xr
import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime, timezone

# Allow imports from backend/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.data.historical_thermal import compute_thermal_history
from training.train import train

def main():
    data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/data.grib"))
    print(f"Reading {data_path}...")
    
    try:
        ds_main = xr.open_dataset(data_path, engine='cfgrib', backend_kwargs={'filter_by_keys': {'stepType': 'instant'}})
        df_main = ds_main.to_dataframe().reset_index()
    except Exception as e:
        print(f"Error reading main variables: {e}")
        return

    try:
        ds_rad = xr.open_dataset(data_path, engine='cfgrib', backend_kwargs={'filter_by_keys': {'stepType': 'accum'}})
        df_rad = ds_rad.to_dataframe().reset_index()
        df = pd.merge(df_main, df_rad, on=['time', 'latitude', 'longitude'], how='left')
    except Exception as e:
        print(f"Could not read radiation variables separately, using main only. Error: {e}")
        df = df_main

    print(f"Total rows: {len(df)}")
    
    # We just pick the first coordinate (lat, lon) to train the model, since the dataset_builder does the same.
    lat = df['latitude'].iloc[0]
    lon = df['longitude'].iloc[0]
    df_loc = df[(df['latitude'] == lat) & (df['longitude'] == lon)].copy()
    df_loc = df_loc.sort_values('time')
    
    # Calculate required variables
    # Temp in C
    if 't2m' in df_loc.columns:
        ta = df_loc['t2m'].values - 273.15
    else:
        ta = np.full(len(df_loc), 25.0)

    # RH from Dewpoint (d2m) and Temp (t2m)
    if 'd2m' in df_loc.columns and 't2m' in df_loc.columns:
        t = df_loc['t2m'].values - 273.15
        td = df_loc['d2m'].values - 273.15
        rh = 100 * (np.exp((17.625 * td) / (243.04 + td)) / np.exp((17.625 * t) / (243.04 + t)))
        rh = np.clip(rh, 0, 100)
    else:
        rh = np.full(len(df_loc), 50.0)

    # Wind speed
    if 'u10' in df_loc.columns and 'v10' in df_loc.columns:
        wind = np.sqrt(df_loc['u10'].values**2 + df_loc['v10'].values**2)
    else:
        wind = np.full(len(df_loc), 2.0)

    # Pressure
    if 'sp' in df_loc.columns:
        pressure = df_loc['sp'].values / 100.0
    else:
        pressure = np.full(len(df_loc), 1013.25)
        
    # Shortwave radiation (Approximate if missing or dropped by cfgrib)
    hours = pd.to_datetime(df_loc['time']).dt.hour.values
    # Rough approximation: 0 at night, sine wave peaking at noon (max ~800 W/m2)
    ghi_approx = np.where((hours >= 6) & (hours <= 18), 
                          800.0 * np.sin((hours - 6) * np.pi / 12), 
                          0.0)
    
    if 'ssrd' in df_loc.columns and not df_loc['ssrd'].isna().all():
        ghi = df_loc['ssrd'].values / 3600.0
        # Fill NaNs with approx
        ghi = np.where(np.isnan(ghi), ghi_approx, ghi)
    else:
        ghi = ghi_approx

    # Build the dictionary for compute_thermal_history
    times = [t.isoformat() + "Z" for t in pd.to_datetime(df_loc['time'])]
    
    raw = {
        "hourly": {
            "time": times,
            "temperature_2m": ta.tolist(),
            "relative_humidity_2m": rh.tolist(),
            "wind_speed_10m": wind.tolist(),
            "surface_pressure": pressure.tolist(),
            "shortwave_radiation": ghi if isinstance(ghi, list) else ghi.tolist(),
        }
    }
    
    print("Computing thermal indices...")
    records = compute_thermal_history(raw, lat, lon)
    
    if not records:
        print("No valid records returned.")
        return
        
    out_df = pd.DataFrame(records)
    out_df["latitude"] = lat
    out_df["longitude"] = lon
    out_df = out_df.dropna(axis=1, how='all')
    
    out_path = os.path.abspath(os.path.join(os.path.dirname(__file__), f"data/thermal_history_{lat}_{lon}_grib.parquet"))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    out_df.to_parquet(out_path, index=False)
    print(f"Saved dataset to {out_path}")
    
    print("Starting training...")
    train(out_path)
    
if __name__ == "__main__":
    main()
