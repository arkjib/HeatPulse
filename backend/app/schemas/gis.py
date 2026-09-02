from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class GISFeatureProperties(BaseModel):
    geographic_id: str
    name: str
    geographic_level: str = Field(..., description="CITY, ZONE, WARD")
    risk_score: Optional[float] = None
    risk_category: str
    hazard_score: float
    exposure_score: Optional[float] = None
    vulnerability_score: Optional[float] = None
    timestamp: str
    forecast_horizon: int = 0
    data_quality: str


class GISFeature(BaseModel):
    type: str = "Feature"
    properties: GISFeatureProperties
    geometry: Optional[Dict[str, Any]] = None


class GISFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: List[GISFeature]
    gis_data_status: str = Field("BOUNDARIES_NOT_CONFIGURED", description="Status of boundary data")
