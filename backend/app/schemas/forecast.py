from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

from app.schemas.weather import Location


class ForecastMetadata(BaseModel):
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    model_status: Literal["MODEL_READY", "MODEL_NOT_TRAINED", "MODEL_ERROR"]
    trained_at: Optional[datetime] = None
    feature_count: Optional[int] = None
    data_period_start: Optional[str] = None
    data_period_end: Optional[str] = None


class ThermalForecastPoint(BaseModel):
    timestamp: datetime
    horizon_hours: int
    # ML predictions (separate models per target)
    wbgt_c: Optional[float] = Field(None, description="ML-predicted WBGT (°C)")
    utci_c: Optional[float] = Field(None, description="ML-predicted UTCI (°C)")
    heat_index_c: Optional[float] = Field(None, description="ML-predicted Heat Index (°C)")
    # Physical deterministic forecast (STEP 3 applied to forecast weather)
    wbgt_physical_c: Optional[float] = Field(None, description="STEP 3 physical WBGT from forecast weather")
    utci_physical_c: Optional[float] = Field(None, description="STEP 3 physical UTCI from forecast weather")
    heat_index_physical_c: Optional[float] = Field(None, description="STEP 3 physical HI from forecast weather")
    # Normalized stress score (0–1), if calculable
    thermal_stress_score: Optional[float] = Field(None, description="Normalized thermal stress 0–1")
    # Uncertainty is reserved; not estimated in v1
    uncertainty: None = None
    confidence_status: str = "NOT_ESTIMATED"


class ThermalForecast(BaseModel):
    location: Location
    horizon_hours: int
    metadata: ForecastMetadata
    forecast: List[ThermalForecastPoint]
    warnings: List[str] = []
