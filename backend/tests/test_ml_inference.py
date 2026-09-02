import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.ml.inference import model_service
import json

client = TestClient(app)

def test_health_check_ml_status():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "ml" in data
    assert data["ml"]["status"] == "READY"
    assert data["ml"]["total_loaded"] == 15

def test_get_models():
    response = client.get("/predict/models")
    assert response.status_code == 200
    data = response.json()
    assert data["status"]["status"] == "READY"
    assert "wbgt_h24" in data["metadata"]
    assert "feature_columns" in data["metadata"]["wbgt_h24"]

def test_predict_endpoint_missing_features():
    req = {
        "latitude": 9.9312,
        "longitude": 76.2673,
        "timestamp": "2026-09-01T12:00:00Z",
        "horizon_hours": 24,
        "weather": {
            "temp_c": 35.0
            # deliberately omitting 89 other features
        }
    }
    response = client.post("/predict", json=req)
    assert response.status_code == 400
    assert "Missing 89 required features" in response.json()["detail"]

def test_predict_valid_features():
    # Construct a dummy weather payload based on required features
    status = model_service.get_status()
    if status["status"] != "READY":
        pytest.skip("Models not ready")
        
    meta = model_service.metadata["wbgt_h24"]
    features = meta["feature_columns"]
    weather = {f: 1.0 for f in features}
    
    req = {
        "latitude": 9.9312,
        "longitude": 76.2673,
        "timestamp": "2026-09-01T12:00:00Z",
        "horizon_hours": 24,
        "weather": weather
    }
    
    response = client.post("/predict", json=req)
    assert response.status_code == 200
    data = response.json()
    assert "wbgt" in data["prediction"]
    assert "utci" in data["prediction"]
    assert "hi" in data["prediction"]
    assert data["risk"]["wbgt"]["category"] in ["LOW", "MODERATE", "HIGH", "VERY_HIGH", "EXTREME"]

def test_predict_single_index():
    meta = model_service.metadata["wbgt_h24"]
    features = meta["feature_columns"]
    weather = {f: 1.0 for f in features}
    
    req = {
        "latitude": 9.9312,
        "longitude": 76.2673,
        "timestamp": "2026-09-01T12:00:00Z",
        "horizon_hours": 48,
        "weather": weather
    }
    
    response = client.post("/predict/utci", json=req)
    assert response.status_code == 200
    data = response.json()
    assert "utci" in data["prediction"]
    assert "wbgt" not in data["prediction"]
    assert "hi" not in data["prediction"]

def test_physical_validation_bounds(monkeypatch):
    meta = model_service.metadata["wbgt_h24"]
    features = meta["feature_columns"]
    weather = {f: 1.0 for f in features}
    
    req = {
        "latitude": 9.9312,
        "longitude": 76.2673,
        "timestamp": "2026-09-01T12:00:00Z",
        "horizon_hours": 24,
        "weather": weather
    }

    # Helper to mock predict output
    def set_mock_predict(val):
        class MockModel:
            def predict(self, X):
                return [val]
        model_service.models["wbgt_h24"] = MockModel()

    # 1. NaN
    set_mock_predict(float('nan'))
    response = client.post("/predict/wbgt", json=req)
    assert response.status_code == 400
    assert "NaN" in response.json()["detail"]

    # 2. Inf
    set_mock_predict(float('inf'))
    response = client.post("/predict/wbgt", json=req)
    assert response.status_code == 400
    assert "Infinity" in response.json()["detail"]

    # 3. Lower-bound violation
    set_mock_predict(-100.1)
    response = client.post("/predict/wbgt", json=req)
    assert response.status_code == 400
    assert "exceeds atmospheric bounds" in response.json()["detail"]

    # 4. Upper-bound violation
    set_mock_predict(100.1)
    response = client.post("/predict/wbgt", json=req)
    assert response.status_code == 400
    assert "exceeds atmospheric bounds" in response.json()["detail"]

    # 5. Normal valid prediction
    set_mock_predict(35.0)
    response = client.post("/predict/wbgt", json=req)
    assert response.status_code == 200
    assert response.json()["prediction"]["wbgt"]["value"] == 35.0
    
    # Reload models to fix the mock
    model_service._initialize()

def test_ood_kochi():
    meta = model_service.metadata["wbgt_h24"]
    features = meta["feature_columns"]
    weather = {f: 1.0 for f in features}
    
    req = {
        "latitude": 10.25,
        "longitude": 76.25,
        "timestamp": "2026-09-01T12:00:00Z",
        "horizon_hours": 24,
        "weather": weather
    }
    response = client.post("/predict", json=req)
    assert response.status_code == 200
    assert response.json()["model_scope"]["status"] == "IN_VALIDATED_REGION"

def test_ood_outside():
    meta = model_service.metadata["wbgt_h24"]
    features = meta["feature_columns"]
    weather = {f: 1.0 for f in features}
    
    req = {
        "latitude": 40.71,
        "longitude": -74.00,
        "timestamp": "2026-09-01T12:00:00Z",
        "horizon_hours": 24,
        "weather": weather
    }
    response = client.post("/predict", json=req)
    assert response.status_code == 200
    assert response.json()["model_scope"]["status"] == "OUTSIDE_VALIDATED_REGION"
