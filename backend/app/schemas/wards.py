from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

class DailyWeather(BaseModel):
    temperature_max_c: float
    temperature_min_c: float
    temperature_mean_c: float
    apparent_temperature_mean_c: float
    humidity_mean_percent: float
    wind_speed_mean_kmh: float
    precipitation_sum_mm: float
    weather_condition: str

class MLPrediction(BaseModel):
    prediction_c: float
    model: str
    rmse_test_error: float
    risk: str

class DailyHeatStress(BaseModel):
    wbgt: MLPrediction
    utci: MLPrediction
    heat_index: MLPrediction

class DailyRisk(BaseModel):
    overall: str
    wbgt: str
    utci: str
    heat_index: str

class WardWeatherData(BaseModel):
    today: DailyWeather
    tomorrow: DailyWeather
    day_plus_2: DailyWeather

class WardHeatStressData(BaseModel):
    today: DailyHeatStress
    tomorrow: DailyHeatStress
    day_plus_2: DailyHeatStress

class WardRiskData(BaseModel):
    today: DailyRisk
    tomorrow: DailyRisk
    day_plus_2: DailyRisk

class WardResponse(BaseModel):
    ward_no: int
    ward_name: str
    latitude: float
    longitude: float
    status: str = "ok"
    error: Optional[str] = None
    weather: Optional[WardWeatherData] = None
    heat_stress: Optional[WardHeatStressData] = None
    risk: Optional[WardRiskData] = None
    provenance: Optional[Dict[str, str]] = None

class WardsWeatherResponse(BaseModel):
    location: str
    timezone: str
    generated_at: datetime
    ward_count: int
    successful_wards: int
    failed_wards: int
    wards: List[WardResponse]
