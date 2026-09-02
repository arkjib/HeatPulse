from fastapi import APIRouter, HTTPException, Depends
from app.schemas.predict import PredictionRequest, PredictionResponse, PredictionDetail, ModelScope
from app.ml.inference import model_service
from app.ml.risk_classifier import classify_risk
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

def _get_model_scope(lat: float, lon: float) -> ModelScope:
    """
    Checks if the requested coordinate is near the strictly validated Kochi/ERA5 grid point (10.25, 76.25).
    Using a roughly 0.5 degree bounding box for the region.
    """
    if (9.75 <= lat <= 10.75) and (75.75 <= lon <= 76.75):
        return ModelScope(
            status="IN_VALIDATED_REGION",
            warning=None
        )
    return ModelScope(
        status="OUTSIDE_VALIDATED_REGION",
        warning="Model performance has been evaluated on unseen chronological Kochi/ERA5 data and may not generalize to this location."
    )

@router.get("/models")
def get_loaded_models():
    """
    Returns the metadata for all currently loaded and available ML models.
    """
    status = model_service.get_status()
    if status["status"] != "READY":
        raise HTTPException(status_code=503, detail="Models are not ready or failed to load.")
    return {
        "status": status,
        "metadata": model_service.metadata
    }

@router.post("", response_model=PredictionResponse)
def predict_all_indices(req: PredictionRequest):
    """
    Predict all thermal indices (WBGT, UTCI, HI) for the given horizon and weather features.
    """
    targets = ["wbgt", "utci", "hi"]
    predictions = {}
    risks = {}

    for target in targets:
        try:
            val, meta = model_service.predict(target, req.horizon_hours, req.weather)
            predictions[target] = PredictionDetail(
                value=val,
                model_used=meta.get("best_candidate", "unknown"),
                artifact_version=meta.get("version", "v1"),
                rmse_test_error=meta.get("val_rmse")
            )
            risks[target] = classify_risk(target, val)
        except ValueError as e:
            logger.warning(f"Prediction failed for {target} at {req.horizon_hours}h: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Internal inference error for {target}: {e}")
            raise HTTPException(status_code=500, detail="Internal inference error")

    return PredictionResponse(
        location={"latitude": req.latitude, "longitude": req.longitude},
        input_timestamp=req.timestamp,
        forecast_horizon_hours=req.horizon_hours,
        prediction=predictions,
        risk=risks,
        model_scope=_get_model_scope(req.latitude, req.longitude)
    )

@router.post("/{index}", response_model=PredictionResponse)
def predict_single_index(index: str, req: PredictionRequest):
    """
    Predict a single thermal index (wbgt, utci, hi) for the given horizon.
    """
    if index not in ["wbgt", "utci", "hi"]:
        raise HTTPException(status_code=404, detail=f"Index '{index}' not found. Supported: wbgt, utci, hi")

    try:
        val, meta = model_service.predict(index, req.horizon_hours, req.weather)
        
        predictions = {
            index: PredictionDetail(
                value=val,
                model_used=meta.get("best_candidate", "unknown"),
                artifact_version=meta.get("version", "v1"),
                rmse_test_error=meta.get("val_rmse")
            )
        }
        risks = {
            index: classify_risk(index, val)
        }

        return PredictionResponse(
            location={"latitude": req.latitude, "longitude": req.longitude},
            input_timestamp=req.timestamp,
            forecast_horizon_hours=req.horizon_hours,
            prediction=predictions,
            risk=risks,
            model_scope=_get_model_scope(req.latitude, req.longitude)
        )
    except ValueError as e:
        logger.warning(f"Prediction failed for {index} at {req.horizon_hours}h: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Internal inference error for {index}: {e}")
        raise HTTPException(status_code=500, detail="Internal inference error")
