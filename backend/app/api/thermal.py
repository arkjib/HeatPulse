from fastapi import APIRouter, Query, HTTPException
from app.schemas.thermal import ThermalStressResult, ThermalInputs, IndexResult, UTCIData, MRTData
from app.data.weather_ingestion import WeatherIngestionService
from app.thermal.heat_index import calculate_heat_index
from app.thermal.radiant_temperature import calculate_mrt
from app.thermal.wbgt import calculate_wbgt
from app.thermal.utci import calculate_utci
from app.thermal.validation import validate_thermal_inputs
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/thermal", tags=["thermal"])
weather_service = WeatherIngestionService()

@router.get("/current", response_model=ThermalStressResult)
async def get_current_thermal(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude")
):
    """
    Get current thermal stress indices (HI, WBGT, UTCI) for a specific location.
    """
    current_weather = await weather_service.get_current_weather(lat, lon)
    w = current_weather.weather
    warnings = []
    
    try:
        validate_thermal_inputs(w.temperature, w.relative_humidity, w.wind_speed)
    except ValueError as e:
        logger.warning(f"Invalid weather data for thermal calculation: {e}")
        warnings.append(str(e))
        
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
    
    mrt_val = mrt_dict.get("value_c")
    if mrt_val is None:
        warnings.append("MRT could not be calculated due to invalid radiation inputs.")
        mrt_val = w.temperature 
    
    hi_dict = calculate_heat_index(w.temperature, w.relative_humidity)
    
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
    
    inputs = ThermalInputs(
        temperature_c=w.temperature,
        relative_humidity_pct=w.relative_humidity,
        wind_speed_ms=w.wind_speed,
        shortwave_radiation_wm2=w.shortwave_radiation,
        direct_radiation_wm2=w.direct_radiation,
        diffuse_radiation_wm2=w.diffuse_radiation,
        dni_wm2=w.direct_normal_irradiance,
        pressure_hpa=w.pressure
    )
    
    return ThermalStressResult(
        location=current_weather,
        timestamp=w.timestamp,
        inputs=inputs,
        heat_index=IndexResult(**hi_dict),
        wbgt=IndexResult(**wbgt_dict),
        utci=UTCIData(**utci_dict),
        mrt=MRTData(**mrt_dict),
        warnings=warnings
    )
