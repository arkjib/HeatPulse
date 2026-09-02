def validate_thermal_inputs(temperature_c: float, relative_humidity: float, wind_speed: float) -> bool:
    """
    Validate that inputs are within physically reasonable bounds for thermal indices.
    """
    if not (-50.0 <= temperature_c <= 60.0):
        raise ValueError(f"Temperature {temperature_c} out of valid bounds (-50, 60)")
    
    if not (0.0 <= relative_humidity <= 100.0):
        raise ValueError(f"Relative humidity {relative_humidity} out of valid bounds (0, 100)")
        
    if wind_speed < 0.0:
        raise ValueError(f"Wind speed {wind_speed} cannot be negative")
        
    return True
