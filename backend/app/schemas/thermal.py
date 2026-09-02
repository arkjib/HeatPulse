from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from .weather import Location

class ThermalInputs(BaseModel):
    temperature_c: float
    relative_humidity_pct: float
    wind_speed_ms: float
    shortwave_radiation_wm2: Optional[float] = None
    direct_radiation_wm2: Optional[float] = None
    diffuse_radiation_wm2: Optional[float] = None
    dni_wm2: Optional[float] = None
    pressure_hpa: float

class IndexResult(BaseModel):
    value_c: Optional[float]
    status: str
    method: str

class UTCIData(IndexResult):
    stress_category: Optional[str] = None

class MRTData(BaseModel):
    value_c: Optional[float]
    status: str
    source: str
    method: str

class ThermalStressResult(BaseModel):
    location: Location
    timestamp: datetime
    inputs: ThermalInputs
    heat_index: IndexResult
    wbgt: IndexResult
    utci: UTCIData
    mrt: MRTData
    warnings: List[str] = Field(default_factory=list)
