import httpx
from typing import Any, Dict
from datetime import date
import logging

logger = logging.getLogger(__name__)

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

HOURLY_VARIABLES = [
    "temperature_2m",
    "relative_humidity_2m",
    "wind_speed_10m",
    "shortwave_radiation",
    "direct_radiation",
    "diffuse_radiation",
    "direct_normal_irradiance",
    "surface_pressure",
]


class HistoricalWeatherClient:
    """
    Async HTTP client for the Open-Meteo Historical Reanalysis API (ERA5).
    Returns hourly meteorological data for a date range.
    """

    async def fetch(
        self,
        lat: float,
        lon: float,
        start: date,
        end: date,
        timeout: float = 60.0,
    ) -> Dict[str, Any]:
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "hourly": ",".join(HOURLY_VARIABLES),
            "wind_speed_unit": "ms",
            "timezone": "UTC",
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(ARCHIVE_URL, params=params, timeout=timeout)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Archive API HTTP error: {e}")
                raise
            except httpx.RequestError as e:
                logger.error(f"Archive API network error: {e}")
                raise
