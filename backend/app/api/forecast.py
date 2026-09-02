"""
forecast.py  (app/api/forecast.py)
------------------------------------
GET /api/v1/forecast/thermal

Flow:
  1. Fetch forecast weather via existing WeatherIngestionService (STEP 2).
  2. Apply STEP 3 thermal engine to each forecast hour (physical path).
  3. Build ML features + generate ML predictions via ForecastingService.
  4. Return ThermalForecast with both ML and physical values.

This endpoint deliberately exposes BOTH the ML predictions AND the
STEP 3 physical deterministic values so the consumer can compare them.
If no trained model exists, returns MODEL_NOT_TRAINED status — no silent fallback.
"""
from datetime import timezone
from typing import List

from fastapi import APIRouter, HTTPException, Query

from app.data.weather_ingestion import WeatherIngestionService
from app.models.forecasting import ForecastingService
from app.schemas.forecast import ForecastMetadata, ThermalForecast, ThermalForecastPoint
from app.schemas.weather import Location
from app.thermal.heat_index import calculate_heat_index
from app.thermal.radiant_temperature import calculate_mrt
from app.thermal.utci import calculate_utci
from app.thermal.wbgt import calculate_wbgt
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/forecast", tags=["forecast"])

weather_service = WeatherIngestionService()
# Service is stateful — loaded once at module import
_forecasting_service = ForecastingService()
_model_status = _forecasting_service.load()


@router.get("/thermal", response_model=ThermalForecast)
async def get_thermal_forecast(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude"),
    days: int = Query(5, ge=1, le=5, description="Forecast horizon in days (1–5)"),
):
    """
    3–5 day thermal stress forecast.

    Returns both:
    - ML predictions (wbgt_c, utci_c, heat_index_c) per horizon
    - Physical deterministic values (*_physical_c) from STEP 3 applied to forecast weather

    If no trained model is available, model_status will be MODEL_NOT_TRAINED
    and ML predictions will be null. Physical values are always calculated.
    """
    horizon_hours = days * 24
    warnings: List[str] = []

    # 1. Fetch forecast weather (existing STEP 2 service)
    try:
        weather_forecast = await weather_service.get_weather_forecast(lat, lon, days=days)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Weather fetch failed: {e}")
        raise HTTPException(status_code=503, detail="Weather provider unavailable")

    forecast_hours_data: List[dict] = []

    # 2. Apply STEP 3 to each forecast hour (physical path)
    for hw in weather_forecast.forecast:
        ta = hw.temperature
        rh = hw.relative_humidity
        wind = hw.wind_speed
        pressure = hw.pressure
        ghi = hw.shortwave_radiation or 0.0
        direct = hw.direct_radiation
        diffuse = hw.diffuse_radiation
        dni = hw.direct_normal_irradiance
        ts = hw.timestamp.replace(tzinfo=timezone.utc) if hw.timestamp.tzinfo is None else hw.timestamp

        mrt = calculate_mrt(
            temperature_c=ta,
            shortwave_rad=ghi,
            direct_rad=direct,
            diffuse_rad=diffuse,
            dni=dni,
            latitude=lat,
            longitude=lon,
            timestamp=ts,
        )
        mrt_val = mrt.get("value_c") if mrt else ta

        hi = calculate_heat_index(ta, rh)
        wbgt = calculate_wbgt(
            temperature_c=ta,
            relative_humidity=rh,
            wind_speed=wind,
            shortwave_rad=ghi,
            latitude=lat,
            longitude=lon,
            timestamp=ts,
            pressure_hpa=pressure,
        )
        utci = calculate_utci(ta, rh, wind, mrt_val)

        forecast_hours_data.append({
            "timestamp": ts,
            "temp_c": ta,
            "rh_pct": rh,
            "wind_ms": wind,
            "pressure_hpa": pressure,
            "ghi_wm2": ghi,
            "direct_rad": direct,
            "diffuse_rad": diffuse,
            "dni": dni,
            "mrt_c": mrt_val,
            # Physical STEP 3 values
            "heat_index_c": hi.get("value_c"),
            "wbgt_c": wbgt.get("value_c"),
            "utci_c": utci.get("value_c"),
        })

    # 3. ML predictions
    ml_predictions = []
    if _model_status == "MODEL_READY":
        try:
            ml_predictions = _forecasting_service.predict(forecast_hours_data, lat, lon)
        except Exception as e:
            logger.error(f"ML prediction failed: {e}")
            warnings.append("ML prediction failed; physical forecast only.")

    # 4. Merge physical + ML into response
    # Index ML predictions by horizon_hours for lookup
    ml_by_horizon = {p["horizon_hours"]: p for p in ml_predictions}

    forecast_points: List[ThermalForecastPoint] = []
    for h in [24, 48, 72, 96, 120]:
        if h > horizon_hours or h >= len(forecast_hours_data):
            continue
        phys = forecast_hours_data[h]
        ml = ml_by_horizon.get(h, {})

        forecast_points.append(ThermalForecastPoint(
            timestamp=phys["timestamp"],
            horizon_hours=h,
            wbgt_c=ml.get("wbgt_c"),
            utci_c=ml.get("utci_c"),
            heat_index_c=ml.get("heat_index_c"),
            wbgt_physical_c=phys.get("wbgt_c"),
            utci_physical_c=phys.get("utci_c"),
            heat_index_physical_c=phys.get("heat_index_c"),
            thermal_stress_score=ml.get("thermal_stress_score"),
        ))

    # 5. Build metadata
    from training.model_registry import get_all_metadata
    all_meta = get_all_metadata()
    first_meta = next(
        (v for k, v in all_meta.items() if not k.startswith("_")), {}
    )

    metadata = ForecastMetadata(
        model_name="SIH26083-ThermalStress-GBM",
        model_version=first_meta.get("version"),
        model_status=_model_status,
        trained_at=first_meta.get("saved_at"),
        feature_count=first_meta.get("feature_count"),
        data_period_start=first_meta.get("data_period", {}).get("train_start") if isinstance(first_meta.get("data_period"), dict) else None,
        data_period_end=first_meta.get("data_period", {}).get("test_end") if isinstance(first_meta.get("data_period"), dict) else None,
    )

    if _model_status != "MODEL_READY":
        warnings.append(
            f"Model status is {_model_status}. ML predictions are not available. "
            "Physical STEP 3 values are still provided."
        )

    return ThermalForecast(
        location=Location(latitude=lat, longitude=lon),
        horizon_hours=horizon_hours,
        metadata=metadata,
        forecast=forecast_points,
        warnings=warnings,
    )

from app.services.forecast import forecast_service
from app.schemas.predict import PredictionResponse

@router.get("", response_model=PredictionResponse)
async def get_ml_forecast(
    latitude: float = Query(..., description="Latitude"),
    longitude: float = Query(..., description="Longitude"),
    horizon_hours: int = Query(72, description="Forecast horizon in hours (24, 48, 72, 96, 120)")
):
    """
    Returns the deterministic ML predictions (WBGT, UTCI, HI) for the specified horizon
    by utilizing actual historical data to construct accurate lag/rolling features.
    """
    if horizon_hours not in [24, 48, 72, 96, 120]:
        raise HTTPException(status_code=400, detail="horizon_hours must be one of: 24, 48, 72, 96, 120")
        
    try:
        return await forecast_service.get_forecast(latitude, longitude, horizon_hours)
    except ValueError as e:
        logger.warning(f"Forecast pipeline error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Internal forecast error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error generating forecast")

@router.get("/sequence", response_model=list[PredictionResponse])
async def get_ml_forecast_sequence(
    latitude: float = Query(..., description="Latitude"),
    longitude: float = Query(..., description="Longitude")
):
    """
    Returns the full timeline sequence (24, 48, 72, 96, 120h) of ML predictions
    for charting and timeline views.
    """
    try:
        return await forecast_service.get_forecast_sequence(latitude, longitude)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Sequence error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error generating forecast sequence")
