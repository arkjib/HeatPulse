import sys
import os
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.ml.inference import model_service
from app.ml.risk_classifier import classify_risk

def main():
    # Make sure models are loaded
    status = model_service.get_status()
    if status["status"] != "READY":
        print(f"Error: Models not ready. Status: {status}")
        return

    print("Model Service is READY.")
    print(f"   Loaded Models: {status['total_loaded']}")
    
    # Let's predict WBGT for 72h horizon
    target = "wbgt"
    horizon = 72
    key = f"{target}_h{horizon}"
    
    meta = model_service.metadata[key]
    feature_cols = meta["feature_columns"]
    
    # We will just construct a dummy weather feature set filled with 2.0
    weather = {f: 2.0 for f in feature_cols}
    # Let's override a few to look realistic
    if "temp_c" in weather: weather["temp_c"] = 38.5
    if "rh_pct" in weather: weather["rh_pct"] = 45.0
    
    val, _ = model_service.predict(target, horizon, weather)
    risk = classify_risk(target, val)
    
    out = {
        "location": {"latitude": 28.6139, "longitude": 77.2090},
        "forecast_horizon_hours": horizon,
        "prediction": {
            target: {
                "value": round(val, 2),
                "model_used": meta.get("best_candidate"),
                "artifact_version": meta.get("version"),
                "rmse_confidence": meta.get("val_rmse")
            }
        },
        "risk": {
            target: {
                "category": risk.category,
                "description": risk.description
            }
        }
    }
    
    print("\n========= PREDICTION OUTPUT =========")
    print(json.dumps(out, indent=2))
    print("=====================================")

if __name__ == "__main__":
    main()
