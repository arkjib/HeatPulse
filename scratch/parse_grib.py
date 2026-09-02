import xarray as xr
import pandas as pd
import sys

def main():
    print("Opening dataset...")
    # Open GRIB file
    ds = xr.open_dataset('data/data.grib', engine='cfgrib')
    print("Dataset opened.")
    
    # Convert to dataframe
    df = ds.to_dataframe().reset_index()
    print("Columns:", df.columns.tolist())
    
    # Typically ERA5 variables in GRIB are t2m, d2m, u10, v10, sp, ssrd, fdir, dswrf, etc.
    # We need to map them to Open-Meteo format for compute_thermal_history:
    # time -> time
    # t2m -> temperature_2m
    # d2m -> dew point or relative humidity
    # u10, v10 -> wind_speed_10m
    # sp -> surface_pressure
    # ssrd -> shortwave_radiation, etc.
    
    # Just save it for now to see what's in it
    df.head().to_csv('scratch/grib_head.csv')
    print("Saved head to scratch/grib_head.csv")

if __name__ == "__main__":
    main()
