from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, Optional

class PredictionRequest(BaseModel):
    latitude: float
    longitude: float
    timestamp: str = Field(..., description="ISO 8601 timestamp of the input data")
    horizon_hours: int = Field(..., description="Forecast horizon in hours: 24, 48, 72, 96, 120")
    weather: Dict[str, float] = Field(..., description="Dictionary containing all required feature columns for the ML model")

    @field_validator('horizon_hours')
    @classmethod
    def validate_horizon(cls, v: int) -> int:
        if v not in [24, 48, 72, 96, 120]:
            raise ValueError("Horizon must be one of: 24, 48, 72, 96, 120")
        return v

class RiskResponse(BaseModel):
    category: str
    description: str

class PredictionDetail(BaseModel):
    value: float
    model_used: str
    artifact_version: str
    rmse_test_error: Optional[float] = Field(None, description="Test RMSE (Typical test error) evaluated on unseen chronological Kochi/ERA5 data. Not a confidence interval.")

class ModelScope(BaseModel):
    validation_region: str = "Kochi, India"
    status: str
    warning: Optional[str] = None

class PredictionResponse(BaseModel):
    location: Dict[str, float]
    input_timestamp: str
    forecast_horizon_hours: int
    prediction: Dict[str, PredictionDetail]
    risk: Dict[str, RiskResponse]
    model_scope: ModelScope
    current_weather: Optional[Dict[str, float]] = None
