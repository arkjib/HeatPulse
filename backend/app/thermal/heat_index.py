from typing import Dict, Any, Union

def calculate_heat_index(temp_c: float, rh: float) -> Dict[str, Any]:
    """
    Calculate the Heat Index in Celsius based on NWS Rothfusz regression.
    """
    if rh < 0 or rh > 100:
        return {"value_c": None, "status": "INVALID_INPUT", "method": "NWS Rothfusz", "reason": "Relative humidity out of bounds"}
        
    # Convert Celsius to Fahrenheit
    t = temp_c * 1.8 + 32.0
    
    if t < 80.0:
        return {"value_c": None, "status": "NOT_APPLICABLE", "method": "NWS Rothfusz", "reason": "Heat Index is not applicable below 80°F (26.7°C)"}

    # Simple HI formula check
    hi = 0.5 * (t + 61.0 + ((t - 68.0) * 1.2) + (rh * 0.094))
    
    if hi >= 80.0:
        # Full Rothfusz regression
        c1 = -42.379
        c2 = 2.04901523
        c3 = 10.14333127
        c4 = -0.22475541
        c5 = -6.83783 * 10**-3
        c6 = -5.481717 * 10**-2
        c7 = 1.22874 * 10**-3
        c8 = 8.5282 * 10**-4
        c9 = -1.99 * 10**-6
        
        hi = (c1 + (c2 * t) + (c3 * rh) + (c4 * t * rh) + (c5 * (t**2)) + 
              (c6 * (rh**2)) + (c7 * (t**2) * rh) + (c8 * t * (rh**2)) + 
              (c9 * (t**2) * (rh**2)))
              
        # Adjustments
        if rh < 13.0 and 80.0 <= t <= 112.0:
            adjustment = ((13.0 - rh) / 4.0) * ((17.0 - abs(t - 95.0)) / 17.0)**0.5
            hi -= adjustment
        elif rh > 85.0 and 80.0 <= t <= 87.0:
            adjustment = ((rh - 85.0) / 10.0) * ((87.0 - t) / 5.0)
            hi += adjustment
            
    # Convert back to Celsius
    hi_c = (hi - 32.0) / 1.8
    
    return {"value_c": round(hi_c, 2), "status": "CALCULATED", "method": "NWS Rothfusz"}
