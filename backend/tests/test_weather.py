import pytest
from httpx import AsyncClient, ASGITransport
from pydantic import ValidationError
from datetime import datetime

from app.main import app
from app.schemas.weather import WeatherBase, Location
from app.data.weather_normalizer import WeatherNormalizer
from app.data.weather_client import WeatherClient
from fastapi import HTTPException

def test_location_validation():
    # Valid
    loc = Location(latitude=45.0, longitude=-90.0)
    assert loc.latitude == 45.0
    
    # Invalid latitude
    with pytest.raises(ValidationError):
        Location(latitude=91.0, longitude=0.0)
        
    # Invalid longitude
    with pytest.raises(ValidationError):
        Location(latitude=0.0, longitude=-181.0)

def test_weather_base_validation():
    timestamp = datetime.now()
    # Valid
    w = WeatherBase(
        timestamp=timestamp, temperature=25.0, relative_humidity=50.0, 
        wind_speed=5.0, shortwave_radiation=800.0, direct_radiation=600.0,
        diffuse_radiation=200.0, direct_normal_irradiance=750.0, pressure=1013.25
    )
    assert w.temperature == 25.0
    
    # Negative wind speed
    with pytest.raises(ValidationError):
        WeatherBase(timestamp=timestamp, temperature=25.0, relative_humidity=50.0, wind_speed=-1.0, pressure=1013.25)
        
    # Negative shortwave radiation
    with pytest.raises(ValidationError):
        WeatherBase(timestamp=timestamp, temperature=25.0, relative_humidity=50.0, wind_speed=5.0, shortwave_radiation=-10.0, pressure=1013.25)
        
    # Missing radiation explicitly allowed
    w_no_solar = WeatherBase(timestamp=timestamp, temperature=25.0, relative_humidity=50.0, wind_speed=5.0, pressure=1013.25)
    assert w_no_solar.shortwave_radiation is None
    assert w_no_solar.direct_radiation is None

def test_weather_normalizer():
    mock_response = {
        "latitude": 52.52,
        "longitude": 13.41,
        "current": {
            "time": "2023-10-10T12:00",
            "temperature_2m": 15.5,
            "relative_humidity_2m": 72,
            "wind_speed_10m": 4.5,
            "shortwave_radiation": 450.0,
            "direct_radiation": 300.0,
            "diffuse_radiation": 150.0,
            "direct_normal_irradiance": 400.0,
            "surface_pressure": 1012.0
        }
    }
    
    normalized = WeatherNormalizer.normalize_current(mock_response)
    assert normalized.latitude == 52.52
    assert normalized.weather.temperature == 15.5
    assert normalized.weather.shortwave_radiation == 450.0
    assert normalized.weather.direct_radiation == 300.0
    assert normalized.weather.pressure == 1012.0

@pytest.mark.asyncio
async def test_get_current_weather_api(mocker):
    # Mock the client fetch so we don't actually hit the external API in tests
    mock_data = {
        "latitude": 28.61,
        "longitude": 77.23,
        "current": {
            "time": "2023-10-10T12:00",
            "temperature_2m": 35.5,
            "relative_humidity_2m": 45,
            "wind_speed_10m": 2.5,
            "shortwave_radiation": 850.0,
            "direct_radiation": 700.0,
            "diffuse_radiation": 150.0,
            "direct_normal_irradiance": 800.0,
            "surface_pressure": 1005.0
        }
    }
    mocker.patch.object(WeatherClient, 'fetch_weather_data', return_value=mock_data)
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/weather/current?lat=28.61&lon=77.23")
    
    assert response.status_code == 200
    data = response.json()
    assert data["latitude"] == 28.61
    assert data["weather"]["temperature"] == 35.5
    assert data["weather"]["shortwave_radiation"] == 850.0
    assert data["weather"]["direct_normal_irradiance"] == 800.0

@pytest.mark.asyncio
async def test_get_current_weather_api_invalid_coords():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/weather/current?lat=95.0&lon=77.23")
    
    # 422 Unprocessable Entity due to validation error
    assert response.status_code == 422 
