import math
from typing import Dict, Any
from pythermalcomfort.models import utci as ptc_utci

def calculate_utci(temperature_c: float, relative_humidity: float, wind_speed: float, mrt: float) -> Dict[str, Any]:
    """
    Calculate UTCI using pythermalcomfort.
    Respects the polynomial applicability limits:
    -50 <= T <= 50
    0.5 <= v <= 17 m/s
    """
    method = "UTCI polynomial"
    
    if relative_humidity < 0 or relative_humidity > 100 or wind_speed < 0:
        return {"value_c": None, "status": "INVALID_INPUT", "stress_category": None, "method": method}
        
    if not (-50.0 <= temperature_c <= 50.0):
        return {"value_c": None, "status": "NOT_APPLICABLE", "stress_category": None, "method": method}
        
    # UTCI wind speed constraint. We do not silently clamp in the library wrapper if we want to be strict,
    # but the UTCI standard practice often caps wind below 0.5 to 0.5 for the formula.
    # The user requested: "Do not silently produce scientifically invalid values outside the supported domain."
    if wind_speed > 17.0:
        return {"value_c": None, "status": "NOT_APPLICABLE", "stress_category": None, "method": method}
        
    # According to UTCI documentation, if v < 0.5, the model is technically out of bounds,
    # but practically v=0.5 is often used as a minimum cap. We'll pass it to pythermalcomfort 
    # with limit_inputs=True and see if it rejects it. If it returns NaN, we return NOT_APPLICABLE.
    
    result = ptc_utci(
        tdb=temperature_c,
        tr=mrt,
        v=wind_speed,
        rh=relative_humidity,
        limit_inputs=True,
        round_output=False
    )
    
    # Convert numpy scalar to python float
    val = float(result.utci)
    
    if math.isnan(val):
        return {"value_c": None, "status": "NOT_APPLICABLE", "stress_category": None, "method": method}
        
    return {
        "value_c": round(val, 2),
        "status": "CALCULATED",
        "stress_category": str(result.stress_category) if result.stress_category else None,
        "method": method
    }
