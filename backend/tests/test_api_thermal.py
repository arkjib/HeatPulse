import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.data.weather_client import WeatherClient

@pytest.mark.asyncio
async def test_get_current_thermal_api(mocker):
    # Mock the client fetch so we don't hit external API
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
        response = await ac.get("/api/v1/thermal/current?lat=28.61&lon=77.23")
    
    assert response.status_code == 200
    data = response.json()
    assert data["location"]["latitude"] == 28.61
    
    assert "heat_index" in data
    assert "wbgt" in data
    assert "utci" in data
    assert "mrt" in data
    
    # Check MRT structure
    assert data["mrt"]["source"] == "derived"
    
    # Check UTCI structure
    assert "stress_category" in data["utci"]
