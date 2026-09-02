import httpx
from typing import Any, Dict
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

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

class OpenMeteoProvider:
    """
    Live weather provider fetching both historical context and future forecasts
    in a single request from Open-Meteo.
    """

    async def fetch(
        self,
        lat: float,
        lon: float,
        past_days: int = 2,
        forecast_days: int = 7,
        timeout: float = 60.0,
    ) -> Dict[str, Any]:
        """
        Fetches hourly meteorological data.
        Past days are required to build lag and rolling features.
        """
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": ",".join(HOURLY_VARIABLES),
            "wind_speed_unit": "ms",
            "timezone": "UTC",
            "past_days": past_days,
            "forecast_days": forecast_days,
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(FORECAST_URL, params=params, timeout=timeout)
                response.raise_for_status()
                data = response.json()
                
                # Normalize response to canonical structure
                return {
                    "latitude": data["latitude"],
                    "longitude": data["longitude"],
                    "hourly": data["hourly"]
                }
            except httpx.HTTPStatusError as e:
                logger.error(f"Open-Meteo API HTTP error: {e}")
                raise
            except httpx.RequestError as e:
                logger.error(f"Open-Meteo API network error: {e}")
                raise
