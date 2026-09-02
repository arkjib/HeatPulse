from fastapi import HTTPException
from app.data.weather_client import WeatherClient
from app.data.weather_normalizer import WeatherNormalizer
from app.schemas.weather import CurrentWeather, WeatherForecast
import logging

logger = logging.getLogger(__name__)

class WeatherIngestionService:
    def __init__(self):
        self.client = WeatherClient()
        self.normalizer = WeatherNormalizer()

    async def get_current_weather(self, lat: float, lon: float) -> CurrentWeather:
        data = await self.client.fetch_weather_data(lat, lon, days=1)
        try:
            return self.normalizer.normalize_current(data)
        except ValueError as e:
            logger.error(f"Normalization error for current weather: {e}")
            raise HTTPException(status_code=502, detail="Invalid data format from weather provider")

    async def get_weather_forecast(self, lat: float, lon: float, days: int = 5) -> WeatherForecast:
        if days < 1 or days > 16:
            raise HTTPException(status_code=400, detail="Forecast days must be between 1 and 16")
            
        data = await self.client.fetch_weather_data(lat, lon, days=days)
        try:
            return self.normalizer.normalize_forecast(data)
        except ValueError as e:
            logger.error(f"Normalization error for weather forecast: {e}")
            raise HTTPException(status_code=502, detail="Invalid data format from weather provider")
