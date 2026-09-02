from typing import List
from pydantic import BaseModel
from app.schemas.predict import PredictionResponse

class ForecastSequence(BaseModel):
    location: dict
    input_timestamp: str
    forecasts: List[PredictionResponse]
