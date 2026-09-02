import logging
import math
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional
import sys
import os
from pathlib import Path

# Need to make sure training is in path if it's imported absolute
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from training.model_registry import load_model, get_all_metadata, STATUS_READY

logger = logging.getLogger(__name__)

class ModelService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.models = {}
        self.metadata = {}
        self.status = "INITIALIZING"
        self._load_all()

    def _load_all(self):
        logger.info("Loading all ML models into memory...")
        all_meta = get_all_metadata()
        if all_meta.get("_status") != STATUS_READY:
            self.status = "MODELS_NOT_READY"
            logger.warning("Model registry is not in READY status.")
            return

        targets = ["wbgt", "utci", "hi"]
        horizons = [24, 48, 72, 96, 120]
        loaded_count = 0

        for target in targets:
            for h in horizons:
                key = f"{target}_h{h}"
                if key in all_meta:
                    try:
                        model, meta = load_model(target, h)
                        self.models[key] = model
                        self.metadata[key] = meta
                        loaded_count += 1
                    except Exception as e:
                        logger.error(f"Failed to load model {key}: {e}")
                else:
                    logger.warning(f"Metadata for {key} missing from registry.")
        
        self.status = "READY" if loaded_count > 0 else "NO_MODELS_LOADED"
        logger.info(f"Loaded {loaded_count} models successfully.")

    def get_status(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "loaded_models": list(self.models.keys()),
            "total_loaded": len(self.models)
        }

    def predict(self, target: str, horizon: int, weather_features: Dict[str, float]) -> Tuple[float, Dict[str, Any]]:
        """
        Runs inference for a given target and horizon using the loaded model.
        Returns (prediction_value, model_metadata).
        Raises ValueError if model is missing or required features are missing.
        """
        key = f"{target}_h{horizon}"
        if key not in self.models:
            raise ValueError(f"Model for {target} at horizon {horizon}h is not loaded.")

        model = self.models[key]
        meta = self.metadata[key]
        feature_cols = meta.get("feature_columns", [])
        
        if not feature_cols:
            raise ValueError(f"Model {key} has no feature_columns in metadata.")

        # Validate inputs
        missing_features = [col for col in feature_cols if col not in weather_features]
        if missing_features:
            # Handle safely: some models can't handle NaN, so we fail fast to avoid internal 500s.
            raise ValueError(f"Missing {len(missing_features)} required features, e.g.: {missing_features[:5]}")

        # Construct input array in the exact order
        X = np.array([[float(weather_features[col]) for col in feature_cols]])
        
        try:
            pred = float(model.predict(X)[0])
        except Exception as e:
            logger.error(f"Inference failed for {key}: {e}")
            raise ValueError(f"Inference computation failed: {e}")

        # Physical sanity validation
        if math.isnan(pred):
            raise ValueError(f"Model predicted NaN for {target}")
        if math.isinf(pred):
            raise ValueError(f"Model predicted Infinity for {target}")
            
        # Tighter physical output validation remains unresolved because scientifically 
        # defensible bounds cannot be established from the existing source material 
        # without inventing arbitrary limits. We enforce absolute atmospheric bounds.
        if pred < -100.0 or pred > 100.0:
            raise ValueError(f"Prediction {pred} for {target} exceeds atmospheric bounds (-100, 100). Tighter physical validation unresolved.")

        return pred, meta

model_service = ModelService()
