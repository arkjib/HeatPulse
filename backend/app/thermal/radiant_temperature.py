from typing import Dict, Any, Optional
from datetime import datetime
import pandas as pd
import pvlib
import math

def calculate_mrt(
    temperature_c: float, 
    shortwave_rad: Optional[float], 
    direct_rad: Optional[float], 
    diffuse_rad: Optional[float], 
    dni: Optional[float],
    latitude: float,
    longitude: float,
    timestamp: datetime
) -> Dict[str, Any]:
    """
    Derive Mean Radiant Temperature (MRT) explicitly using solar geometry and radiation fields.
    Methodology follows the standard ASHRAE 55 / MENEX model for outdoor MRT.
    """
    method = "ASHRAE/MENEX Solar Geometry MRT Model"
    
    # Validate inputs
    if any(r is not None and r < 0 for r in [shortwave_rad, direct_rad, diffuse_rad, dni]):
        return {"value_c": None, "status": "INVALID_INPUT", "source": "derived", "method": method}
        
    # If no sun, MRT is approx Ta
    if shortwave_rad is None or shortwave_rad <= 0.0:
        return {
            "value_c": float(round(temperature_c, 2)),
            "status": "CALCULATED",
            "source": "derived",
            "method": method
        }
        
    try:
        # 1. Calculate Solar Zenith Angle using pvlib
        if timestamp.tzinfo is None:
            # Assume UTC if naive
            dt = pd.Timestamp(timestamp, tz='UTC')
        else:
            dt = pd.Timestamp(timestamp)
            
        solpos = pvlib.solarposition.get_solarposition(dt, latitude, longitude)
        zenith_deg = solpos['zenith'].iloc[0]
        
        if zenith_deg >= 90:
            # Sun is below horizon, no solar load
            return {
                "value_c": float(round(temperature_c, 2)),
                "status": "CALCULATED",
                "source": "derived",
                "method": method
            }
            
        zenith_rad = math.radians(zenith_deg)
        
        # 2. Projected Area Factor (f_p) for a standing person
        # Approximated via Jendritzky et al.
        f_p = 0.308 * math.cos(zenith_rad) + 0.043 * math.sin(zenith_rad)
        
        # 3. Parameters
        alpha_sw = 0.7       # shortwave absorptivity of clothing/skin
        epsilon = 0.95       # emissivity
        sigma = 5.67e-8      # Stefan-Boltzmann constant (W/m2K4)
        f_eff = 0.725        # effective radiating area of human body
        albedo = 0.2         # standard grass/asphalt albedo
        
        # We prefer explicitly provided DNI and Diffuse, otherwise fallback to GHI partition
        active_dni = dni if dni is not None else direct_rad
        if active_dni is None:
            # Rough fallback if only GHI is available (not expected per instructions)
            active_dni = shortwave_rad * 0.8
            
        active_diffuse = diffuse_rad if diffuse_rad is not None else (shortwave_rad - (active_dni * math.cos(zenith_rad)))
        if active_diffuse < 0:
            active_diffuse = 0
            
        # 4. Total Absorbed Solar Radiation (E_solar)
        # E_solar = alpha * f_eff * (f_p * DNI + 0.5 * Diffuse + 0.5 * albedo * GHI)
        e_solar = alpha_sw * f_eff * (f_p * active_dni + 0.5 * active_diffuse + 0.5 * albedo * shortwave_rad)
        
        # 5. Calculate MRT balancing longwave and shortwave
        # MRT^4 = (Ta + 273.15)^4 + E_solar / (epsilon * sigma)
        ta_k = temperature_c + 273.15
        mrt_k4 = (ta_k ** 4) + (e_solar / (epsilon * sigma))
        mrt_c = (mrt_k4 ** 0.25) - 273.15
        
        return {
            "value_c": float(round(mrt_c, 2)),
            "status": "CALCULATED",
            "source": "derived",
            "method": method
        }
        
    except Exception as e:
        return {"value_c": None, "status": "NOT_APPLICABLE", "source": "derived", "method": method}
