from fastapi import APIRouter, Query, HTTPException
from datetime import datetime, timezone
from app.schemas.risk import ConsolidatedRiskResponse
from app.models.health_risk_model import HealthRiskModel
from app.api.forecast import get_thermal_forecast
from app.data.weather_ingestion import WeatherIngestionService
from app.thermal.heat_index import calculate_heat_index
from app.thermal.radiant_temperature import calculate_mrt
from app.thermal.wbgt import calculate_wbgt
from app.thermal.utci import calculate_utci

router = APIRouter(prefix="/risk", tags=["risk"])
risk_model = HealthRiskModel()
weather_service = WeatherIngestionService()


@router.get("/current", response_model=ConsolidatedRiskResponse)
async def get_current_risk(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude")
):
    """
    Computes current health risk for a location by dynamically fetching weather
    and evaluating Thermal Stress, Vulnerability, and Heatwave Outlook.
    """
    current_weather = await weather_service.get_current_weather(lat, lon)
    if not current_weather or not current_weather.weather:
        raise HTTPException(status_code=404, detail="Weather data unavailable")
        
    w = current_weather.weather
    
    mrt_dict = calculate_mrt(
        temperature_c=w.temperature,
        shortwave_rad=w.shortwave_radiation,
        direct_rad=w.direct_radiation,
        diffuse_rad=w.diffuse_radiation,
        dni=w.direct_normal_irradiance,
        latitude=lat,
        longitude=lon,
        timestamp=w.timestamp
    )
    mrt_val = mrt_dict.get("value_c") if mrt_dict.get("value_c") is not None else w.temperature

    wbgt_dict = calculate_wbgt(
        temperature_c=w.temperature,
        relative_humidity=w.relative_humidity,
        wind_speed=w.wind_speed,
        shortwave_rad=w.shortwave_radiation,
        latitude=lat,
        longitude=lon,
        timestamp=w.timestamp,
        pressure_hpa=w.pressure
    )
    
    utci_dict = calculate_utci(
        temperature_c=w.temperature,
        relative_humidity=w.relative_humidity,
        wind_speed=w.wind_speed,
        mrt=mrt_val
    )
    
    hi_dict = calculate_heat_index(w.temperature, w.relative_humidity)

    return risk_model.compute_risk(
        lat=lat,
        lon=lon,
        timestamp=str(w.timestamp),
        wbgt_data=wbgt_dict,
        utci_data=utci_dict,
        hi_data=hi_dict,
        max_temp_c=w.temperature # Using current temp as a proxy for max if current, though forecast should provide real max
    )

@router.get("/forecast", response_model=list[ConsolidatedRiskResponse])
async def get_forecast_risk(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    days: int = Query(5, description="Days to forecast")
):
    """
    Returns 5-day risk forecast.
    """
    thermal_forecasts = await get_thermal_forecast(lat=lat, lon=lon, days=days)
    
    responses = []
    # get_thermal_forecast returns ThermalForecast object containing list of ThermalForecastPoint
    for tf in thermal_forecasts.forecast:
        # Wrap the ml predictions or physical values into dicts suitable for compute_risk
        
        # Here tf is ThermalForecastPoint
        wbgt_dict = {
            "value_c": tf.wbgt_c if tf.wbgt_c is not None else tf.wbgt_physical_c,
            "status": "CALCULATED" if (tf.wbgt_c is not None or tf.wbgt_physical_c is not None) else "NOT_APPLICABLE",
            "method": "ML Model" if tf.wbgt_c is not None else "Physical"
        }
        
        utci_dict = {
            "value_c": tf.utci_c if tf.utci_c is not None else tf.utci_physical_c,
            "status": "CALCULATED" if (tf.utci_c is not None or tf.utci_physical_c is not None) else "NOT_APPLICABLE",
            "method": "ML Model" if tf.utci_c is not None else "Physical"
        }
        
        hi_dict = {
            "value_c": tf.heat_index_c if tf.heat_index_c is not None else tf.heat_index_physical_c,
            "status": "CALCULATED" if (tf.heat_index_c is not None or tf.heat_index_physical_c is not None) else "NOT_APPLICABLE",
            "method": "ML Model" if tf.heat_index_c is not None else "Physical",
            "reason": "Forecasted"
        }
        
        risk = risk_model.compute_risk(
            lat=lat,
            lon=lon,
            timestamp=str(tf.timestamp),
            wbgt_data=wbgt_dict,
            utci_data=utci_dict,
            hi_data=hi_dict,
            max_temp_c=None # Needs proper extraction from weather forecast if we want true daily max for HW
        )
        responses.append(risk)
        
    return responses
