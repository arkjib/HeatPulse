import httpx
from typing import Any, Dict
from fastapi import HTTPException
import logging
import time

logger = logging.getLogger(__name__)

class WeatherClient:
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    _cache = {}
    _circuit_breaker_until = 0

    async def fetch_weather_data(self, lat: float, lon: float, days: int = 5) -> Dict[str, Any]:
        cache_key = f"{lat}_{lon}_{days}"
        now = time.time()
        
        # 1. Return cache if fresh (3600 seconds)
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            if now - entry['timestamp'] < 3600:
                return entry['data']

        # Circuit breaker: if we hit a rate limit/network error recently, return fallback immediately
        if now < type(self)._circuit_breaker_until:
            return self._generate_fallback(lat, lon, days)

        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,shortwave_radiation,direct_radiation,diffuse_radiation,direct_normal_irradiance,surface_pressure",
            "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,shortwave_radiation,direct_radiation,diffuse_radiation,direct_normal_irradiance,surface_pressure",
            "forecast_days": days,
            "wind_speed_unit": "ms"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.BASE_URL, params=params, timeout=5.0)
                response.raise_for_status()
                data = response.json()
                
                # 2. Update cache on success
                self._cache[cache_key] = {'timestamp': now, 'data': data}
                return data
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error occurred while fetching weather data: {e}")
                type(self)._circuit_breaker_until = now + 600  # Trip breaker for 10 minutes
                if cache_key in self._cache:
                    return self._cache[cache_key]['data']
                return self._generate_fallback(lat, lon, days)
                
            except httpx.RequestError as e:
                logger.error(f"Network error occurred while fetching weather data: {e}")
                type(self)._circuit_breaker_until = now + 600  # Trip breaker for 10 minutes
                if cache_key in self._cache:
                    return self._cache[cache_key]['data']
                return self._generate_fallback(lat, lon, days)
                
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                if cache_key in self._cache:
                    return self._cache[cache_key]['data']
                return self._generate_fallback(lat, lon, days)

    def _generate_fallback(self, lat: float, lon: float, days: int) -> Dict[str, Any]:
        logger.warning(f"Using synthetic fallback weather for {lat},{lon} due to API failure")
        from datetime import datetime, timedelta, timezone
        
        # Build hourly arrays
        now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        times = [(now + timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M") for i in range(days * 24)]
        
        # Synthetic hot humid coastal conditions
        temps = [31.5 + (i % 24 - 12) * -0.2 for i in range(days * 24)]
        rh = [75.0 + (i % 24 - 12) * 0.5 for i in range(days * 24)]
        
        return {
            "latitude": lat,
            "longitude": lon,
            "timezone": "UTC",
            "current": {
                "time": times[0],
                "temperature_2m": 31.5,
                "relative_humidity_2m": 75.0,
                "wind_speed_10m": 4.5,
                "shortwave_radiation": 600,
                "direct_radiation": 400,
                "diffuse_radiation": 200,
                "direct_normal_irradiance": 500,
                "surface_pressure": 1012
            },
            "hourly": {
                "time": times,
                "temperature_2m": temps,
                "relative_humidity_2m": rh,
                "wind_speed_10m": [4.5] * len(times),
                "shortwave_radiation": [600 if 6 <= (i%24) <= 18 else 0 for i in range(len(times))],
                "direct_radiation": [400 if 6 <= (i%24) <= 18 else 0 for i in range(len(times))],
                "diffuse_radiation": [200 if 6 <= (i%24) <= 18 else 0 for i in range(len(times))],
                "direct_normal_irradiance": [500 if 6 <= (i%24) <= 18 else 0 for i in range(len(times))],
                "surface_pressure": [1012] * len(times)
            }
        }
