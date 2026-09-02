from fastapi import APIRouter, Query, HTTPException
from app.schemas.weather import CurrentWeather, WeatherForecast
from app.data.weather_ingestion import WeatherIngestionService

router = APIRouter(prefix="/weather", tags=["weather"])
weather_service = WeatherIngestionService()

@router.get("/current", response_model=CurrentWeather)
async def get_current_weather(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude")
):
    """
    Get current weather for a specific location.
    """
    return await weather_service.get_current_weather(lat, lon)

@router.get("/forecast", response_model=WeatherForecast)
async def get_weather_forecast(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude"),
    days: int = Query(5, ge=1, le=14, description="Number of days for forecast")
):
    """
    Get hourly weather forecast for a specific location up to 14 days.
    """
    return await weather_service.get_weather_forecast(lat, lon, days)
