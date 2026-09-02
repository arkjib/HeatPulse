import pandas as pd
from typing import Dict, Any, List
from datetime import datetime, timezone
import logging

from app.weather.open_meteo import OpenMeteoProvider
from app.weather.history import weather_cache
from app.data.historical_thermal import compute_thermal_history
from app.ml.inference import model_service
from app.ml.risk_classifier import classify_risk
from app.schemas.predict import PredictionResponse, PredictionDetail, RiskResponse, ModelScope
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from training.feature_engineering import build_features, get_feature_columns

logger = logging.getLogger(__name__)

def _get_model_scope(lat: float, lon: float) -> ModelScope:
    if (9.75 <= lat <= 10.75) and (75.75 <= lon <= 76.75):
        return ModelScope(status="IN_VALIDATED_REGION", warning=None)
    return ModelScope(
        status="OUTSIDE_VALIDATED_REGION",
        warning="Model performance has been evaluated on unseen chronological Kochi/ERA5 data and may not generalize to this location."
    )

class ForecastService:
    def __init__(self):
        self.provider = OpenMeteoProvider()

    async def get_forecast(self, lat: float, lon: float, horizon_hours: int) -> PredictionResponse:
        """
        Coordinates the pipeline:
        1. Fetch current + past weather (cached if recently requested)
        2. Compute historical thermal indices (STEP 3 engine)
        3. Build exactly 90 lag/rolling ML features
        4. Predict target values via ModelService
        5. Apply risk classifications
        6. Return formatted schema
        """
        # 1. Fetch live weather (we need past_days=2 to satisfy the 24h lag/rolling requirements)
        # We don't need future forecast days because the ML models autoregressively predict T+h from T.
        raw_data = weather_cache.get(lat, lon)
        if not raw_data:
            logger.info(f"Cache miss for {lat},{lon}. Fetching from Open-Meteo...")
            raw_data = await self.provider.fetch(lat, lon, past_days=2, forecast_days=1)
            weather_cache.set(lat, lon, raw_data)
        
        # 2. Convert raw provider data to thermal history records
        records = compute_thermal_history(raw_data, lat, lon)
        if not records:
            raise ValueError("Failed to compute thermal history from weather data.")
            
        df = pd.DataFrame(records)
        df["latitude"] = lat
        df["longitude"] = lon
        
        # Drop columns that are entirely NaN (matching the training pipeline logic for missing radiation data)
        df = df.dropna(axis=1, how='all')

        # 3. Build features
        fe_df = build_features(df, lat, lon)
        
        # 4. Extract the MOST RECENT valid hour
        # Since build_features generates lags, the first 24 rows will have NaNs and be dropped.
        # We want the absolute latest row representing "current time" T to predict T+horizon.
        feature_cols = get_feature_columns(fe_df)
        fe_df = fe_df.dropna(subset=feature_cols).reset_index(drop=True)
        
        if len(fe_df) == 0:
            raise ValueError("Insufficient historical data to build the 90 model features.")
            
        latest_row = fe_df.iloc[-1]
        input_timestamp = str(latest_row["timestamp"])
        
        weather_features = latest_row[feature_cols].to_dict()
        
        # 5. Run ML inference for all indices
        targets = ["wbgt", "utci", "hi"]
        predictions = {}
        risks = {}
        
        for target in targets:
            val, meta = model_service.predict(target, horizon_hours, weather_features)
            predictions[target] = PredictionDetail(
                value=val,
                model_used=meta.get("best_candidate", "unknown"),
                artifact_version=meta.get("version", "v1"),
                rmse_test_error=meta.get("test_metrics", {}).get("rmse") or meta.get("val_rmse")
            )
            risk_cat = classify_risk(target, val)
            risks[target] = RiskResponse(category=risk_cat.category, description=risk_cat.description)

        return PredictionResponse(
            location={"latitude": lat, "longitude": lon},
            input_timestamp=input_timestamp,
            forecast_horizon_hours=horizon_hours,
            prediction=predictions,
            risk=risks,
            model_scope=_get_model_scope(lat, lon),
            current_weather={
                "temp_c": weather_features.get("temp_c"),
                "rh_pct": weather_features.get("rh_pct"),
                "wind_ms": weather_features.get("wind_ms"),
                "pressure_hpa": weather_features.get("pressure_hpa"),
                "ghi_wm2": weather_features.get("ghi_wm2")
            }
        )

    async def get_forecast_sequence(self, lat: float, lon: float) -> List[PredictionResponse]:
        """Runs the pipeline for all horizons (24, 48, 72, 96, 120) and returns the full timeline sequence."""
        # 1. Fetch live weather (cached)
        raw_data = weather_cache.get(lat, lon)
        if not raw_data:
            raw_data = await self.provider.fetch(lat, lon, past_days=2, forecast_days=1)
            weather_cache.set(lat, lon, raw_data)
        
        records = compute_thermal_history(raw_data, lat, lon)
        if not records:
            raise ValueError("Failed to compute thermal history from weather data.")
            
        df = pd.DataFrame(records)
        df["latitude"] = lat
        df["longitude"] = lon
        df = df.dropna(axis=1, how='all')

        fe_df = build_features(df, lat, lon)
        feature_cols = get_feature_columns(fe_df)
        fe_df = fe_df.dropna(subset=feature_cols).reset_index(drop=True)
        
        if len(fe_df) == 0:
            raise ValueError("Insufficient historical data to build the 90 model features.")
            
        latest_row = fe_df.iloc[-1]
        input_timestamp = str(latest_row["timestamp"])
        weather_features = latest_row[feature_cols].to_dict()
        
        horizons = [24, 48, 72, 96, 120]
        targets = ["wbgt", "utci", "hi"]
        
        results = []
        for h in horizons:
            predictions = {}
            risks = {}
            for target in targets:
                try:
                    val, meta = model_service.predict(target, h, weather_features)
                    predictions[target] = PredictionDetail(
                        value=val,
                        model_used=meta.get("best_candidate", "unknown"),
                        artifact_version=meta.get("version", "v1"),
                        rmse_test_error=meta.get("test_metrics", {}).get("rmse") or meta.get("val_rmse")
                    )
                    risk_cat = classify_risk(target, val)
                    risks[target] = RiskResponse(category=risk_cat.category, description=risk_cat.description)
                except Exception as e:
                    logger.error(f"Error predicting {target} for {h}h: {e}")
                    
            if predictions:
                results.append(PredictionResponse(
                    location={"latitude": lat, "longitude": lon},
                    input_timestamp=input_timestamp,
                    forecast_horizon_hours=h,
                    prediction=predictions,
                    risk=risks,
                    model_scope=_get_model_scope(lat, lon),
                    current_weather={
                        "temp_c": weather_features.get("temp_c"),
                        "rh_pct": weather_features.get("rh_pct"),
                        "wind_ms": weather_features.get("wind_ms"),
                        "pressure_hpa": weather_features.get("pressure_hpa"),
                        "ghi_wm2": weather_features.get("ghi_wm2")
                    }
                ))
                
        return results

forecast_service = ForecastService()
