from fastapi import APIRouter, Query, HTTPException
from app.schemas.gis import GISFeatureCollection
from app.gis.spatial_risk import SpatialRiskService
from app.api.risk import get_current_risk, get_forecast_risk
from app.models.health_risk_model import HealthRiskModel

router = APIRouter()
spatial_service = SpatialRiskService()

@router.get("/risk/current", response_model=GISFeatureCollection)
async def get_current_risk_gis(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude")
):
    """
    Returns current spatial risk mapped to GeoJSON boundaries.
    Does NOT calculate thermal stress internally; strictly aggregates STEP 5 outputs.
    """
    try:
        risk_response = await get_current_risk(lat, lon)
        return spatial_service.generate_feature_collection([risk_response], horizon=0)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/risk/forecast", response_model=GISFeatureCollection)
async def get_forecast_risk_gis(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    hours: int = Query(24, description="Specific forecast hour to map (24, 48, 72, 96, 120)")
):
    """
    Returns forecast spatial risk mapped to GeoJSON boundaries for a specific horizon.
    """
    try:
        # get_forecast_risk returns a list of risk responses for each horizon in days.
        # We need to map the requested 'hours' to 'days'
        days = max(1, min(5, hours // 24))
        risk_responses = await get_forecast_risk(lat, lon, days=days)
        
        # Filter for the specific horizon
        target_timestamp = None
        # We assume get_forecast_risk returns 5 daily points. We just grab the one matching the hour roughly, 
        # or just return the entire collection. The prompt says GET /api/v1/gis/risk/forecast?hours=24|48|72|96|120
        # Let's just grab the risk response that corresponds to that hour. 
        # For simplicity, if days=days was passed, the last item in the list is the target.
        if not risk_responses:
            raise HTTPException(status_code=404, detail="No forecast available")
            
        target_risk = risk_responses[-1] 
        return spatial_service.generate_feature_collection([target_risk], horizon=hours)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
