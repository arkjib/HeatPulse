from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime

class Location(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")

class WeatherBase(BaseModel):
    timestamp: datetime
    temperature: float = Field(..., ge=-100, le=100, description="Air temperature in Celsius")
    relative_humidity: float = Field(..., ge=0, le=100, description="Relative humidity in percentage")
    wind_speed: float = Field(..., ge=0, description="Wind speed in m/s")
    shortwave_radiation: Optional[float] = Field(None, ge=0, description="Shortwave radiation (GHI) in W/m²")
    direct_radiation: Optional[float] = Field(None, ge=0, description="Direct radiation in W/m²")
    diffuse_radiation: Optional[float] = Field(None, ge=0, description="Diffuse radiation in W/m²")
    direct_normal_irradiance: Optional[float] = Field(None, ge=0, description="Direct normal irradiance (DNI) in W/m²")
    pressure: float = Field(..., ge=800, le=1100, description="Atmospheric pressure in hPa")

class CurrentWeather(Location):
    weather: WeatherBase

class HourlyWeather(WeatherBase):
    pass

class WeatherForecast(Location):
    forecast: List[HourlyWeather]
