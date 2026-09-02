from typing import List, Optional
from pydantic import BaseModel, Field

class ActionRecommendation(BaseModel):
    action_id: str
    description: str

class AlertRuleDefinition(BaseModel):
    rule_id: str
    condition_description: str
    severity: str
    recommended_actions: List[ActionRecommendation]
    explanation: str

class AlertPayload(BaseModel):
    fingerprint: str
    geographic_level: str
    geographic_id: str
    alert_category: str
    rule_id: str
    forecast_start: str
    forecast_end: str
    risk_score: Optional[float] = None
    
    recommended_actions: List[str]
    alert_message: str
    
    alert_lifecycle: str = Field("PENDING", description="CREATED, PENDING, READY, SENT, FAILED, ACKNOWLEDGED, EXPIRED, CANCELLED")
    execution_status: str = Field("RECOMMENDED", description="RECOMMENDED, ACKNOWLEDGED, EXECUTED")
