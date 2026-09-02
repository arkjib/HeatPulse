import math
from typing import Dict, Any
import lwbgt
from datetime import datetime, timezone

def calculate_wbgt(
    temperature_c: float, 
    relative_humidity: float, 
    wind_speed: float, 
    shortwave_rad: float,
    latitude: float,
    longitude: float,
    timestamp: datetime,
    pressure_hpa: float = 1013.25
) -> Dict[str, Any]:
    """
    Calculate Outdoor WBGT using the heat balance methodology of Liljegren et al. (2008).
    
    This implementation leverages the `lwbgt` C-extension library, which is a highly 
    validated, dependency-free, direct port of James C. Liljegren's original model.
    It solves the complex radiative and convective heat-mass transfer balances internally.
    """
    method = "Liljegren et al. Heat Balance Solver (lwbgt)"
    
    if relative_humidity < 0 or relative_humidity > 100 or wind_speed < 0:
        return {"value_c": None, "status": "INVALID_INPUT", "method": method}
        
    try:
        # Convert timestamp to UTC components for solar geometry
        dt_utc = timestamp.astimezone(timezone.utc)
        
        inp = lwbgt.Input(
            year=dt_utc.year,
            month=dt_utc.month,
            day=dt_utc.day,
            hour=dt_utc.hour,
            minute=dt_utc.minute,
            gmt_offset_hours=0,
            averaging_minutes=0,
            urban=0, # 0 = rural/meteorological wind profile
            latitude_deg_north=float(latitude),
            longitude_deg_east=float(longitude),
            solar_w_m2=float(shortwave_rad),
            pressure_hpa=float(pressure_hpa),
            air_temperature_c=float(temperature_c),
            relative_humidity_percent=float(relative_humidity),
            wind_speed_m_s=float(wind_speed),
            wind_height_m=10.0, # Meteorological standard height
            vertical_temperature_difference_c=0.0
        )
        
        result = lwbgt.calculate(inp)
        
        # Valid status is 0
        if result.status != 0:
            return {"value_c": None, "status": "NOT_APPLICABLE", "method": method}
            
        return {
            "value_c": float(round(result.wbgt_c, 2)),
            "tg_c": float(round(result.globe_temperature_c, 2)),
            "tnwb_c": float(round(result.natural_wet_bulb_c, 2)),
            "status": "CALCULATED",
            "method": method
        }
    except Exception as e:
        return {"value_c": None, "status": "NOT_APPLICABLE", "method": method}
