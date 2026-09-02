from typing import List
from fastapi import APIRouter, Query, HTTPException
from app.schemas.alerts import AlertPayload
from app.api.gis import get_current_risk_gis, get_forecast_risk_gis
from app.alerts.action_engine import ActionEngine
from app.alerts.notification_service import NotificationService

router = APIRouter()
action_engine = ActionEngine()
notification_service = NotificationService()

@router.get("/current", response_model=List[AlertPayload])
async def get_current_alerts(
    lat: float = Query(...),
    lon: float = Query(...)
):
    """
    Returns deduplicated alerts based on current risk. 
    NEVER sends notifications.
    """
    gis_collection = await get_current_risk_gis(lat, lon)
    if not gis_collection.features:
        return []
    
    timestamp = gis_collection.features[0].properties.timestamp
    alerts = action_engine.generate_alerts(gis_collection, forecast_start=timestamp, forecast_end=timestamp)
    return alerts

@router.get("/forecast", response_model=List[AlertPayload])
async def get_forecast_alerts(
    lat: float = Query(...),
    lon: float = Query(...),
    hours: int = Query(24)
):
    """
    Returns deduplicated alerts for a specific forecast horizon.
    NEVER sends notifications.
    """
    gis_collection = await get_forecast_risk_gis(lat, lon, hours)
    if not gis_collection.features:
        return []
    
    timestamp = gis_collection.features[0].properties.timestamp
    alerts = action_engine.generate_alerts(gis_collection, forecast_start=timestamp, forecast_end=timestamp)
    return alerts

@router.post("/preview", response_model=List[AlertPayload])
async def preview_alerts(
    lat: float = Query(...),
    lon: float = Query(...)
):
    """
    Generates an alert payload for testing and preview without sending.
    """
    gis_collection = await get_current_risk_gis(lat, lon)
    if not gis_collection.features:
        return []
        
    timestamp = gis_collection.features[0].properties.timestamp
    alerts = action_engine.generate_alerts(gis_collection, forecast_start=timestamp, forecast_end=timestamp)
    
    # Process through notification service (which will skip sending since NOTIFICATION_ENABLED=False by default)
    processed = [notification_service.dispatch(a) for a in alerts]
    return processed
