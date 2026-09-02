"""
dataset_builder.py
------------------
CLI script that:
  1. Fetches hourly historical weather from Open-Meteo archive (ERA5)
  2. Applies the STEP 3 thermal engine to each hour
  3. Saves the enriched dataset to training/data/ as a Parquet file

Usage:
  cd backend
  python training/dataset_builder.py \\
      --lat 28.61 --lon 77.23 \\
      --start 2020-01-01 --end 2023-12-31

Output:
  training/data/thermal_history_28.61_77.23_2020-01-01_2023-12-31.parquet
"""
import argparse
import asyncio
import logging
import sys
from datetime import date, datetime
from pathlib import Path

import pandas as pd

# Allow running from backend/ directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.data.historical_client import HistoricalWeatherClient
from app.data.historical_thermal import compute_thermal_history

DATA_DIR = Path(__file__).parent / "data"
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def build_dataset(
    lat: float,
    lon: float,
    start: date,
    end: date,
) -> Path:
    """Fetch, compute, and save the thermal history dataset."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    client = HistoricalWeatherClient()
    logger.info(f"Fetching ERA5 data for ({lat}, {lon}) from {start} to {end}...")
    raw = await client.fetch(lat, lon, start, end, timeout=120.0)

    logger.info("Computing thermal indices via STEP 3 engine...")
    records = compute_thermal_history(raw, lat, lon)

    if not records:
        logger.error("No valid records returned. Dataset not saved.")
        sys.exit(1)

    df = pd.DataFrame(records)
    df["latitude"] = lat
    df["longitude"] = lon

    out_path = DATA_DIR / f"thermal_history_{lat}_{lon}_{start}_{end}.parquet"
    df.to_parquet(out_path, index=False)
    logger.info(f"Saved {len(df)} rows to {out_path}")

    # Quick summary
    missing = df.isnull().mean() * 100
    logger.info("Missing data %:")
    for col, pct in missing.items():
        if pct > 0:
            logger.info(f"  {col}: {pct:.1f}%")

    return out_path


def main():
    parser = argparse.ArgumentParser(description="Build SIH26083 thermal history dataset")
    parser.add_argument("--lat", type=float, required=True)
    parser.add_argument("--lon", type=float, required=True)
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--end", type=date.fromisoformat, required=True)
    args = parser.parse_args()

    asyncio.run(build_dataset(args.lat, args.lon, args.start, args.end))


if __name__ == "__main__":
    main()
