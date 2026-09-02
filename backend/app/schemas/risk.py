from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class RiskComponent(BaseModel):
    raw_value: Optional[float] = Field(None, description="Raw input value")
    unit: Optional[str] = Field(None, description="Unit of the raw value")
    normalized_value: Optional[float] = Field(None, description="Normalized score 0-100")
    source: str = Field(..., description="Source of the data")
    status: str = Field(..., description="AVAILABLE, MISSING, ESTIMATED, NOT_APPLICABLE")
    geographic_level: str = Field(..., description="CITY, ZONE, WARD, OTHER")
    is_real_data: bool = Field(..., description="False if this is synthetic/demo data")

class ThermalIndexRisk(BaseModel):
    value: Optional[float] = None
    status: str
    category: str
    description: str
    reason: Optional[str] = None
    method: str

class ThermalStressResponse(BaseModel):
    overall_thermal_stress: str
    dominant_index: str
    indices: Dict[str, ThermalIndexRisk]

class EstimatedHealthRisk(BaseModel):
    risk_level: str
    dominant_driver: str
    explanation: List[str]

class HeatwaveOutlook(BaseModel):
    status: str
    explanation: List[str]

class ConsolidatedRiskResponse(BaseModel):
    location: dict
    timestamp: str
    thermal_stress: ThermalStressResponse
    estimated_health_risk: EstimatedHealthRisk
    heatwave_outlook: HeatwaveOutlook
