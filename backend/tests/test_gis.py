import pytest
from app.gis.ward_mapping import WardMappingService
from app.gis.spatial_risk import SpatialRiskService
from app.schemas.risk import ConsolidatedRiskResponse
import json

def test_geometry_null_when_unavailable():
    service = SpatialRiskService()
    
    risk_data = {
        "location": {"lat": 9.965261, "lon": 76.248245},
        "timestamp": "2023-01-01T12:00:00Z",
        "thermal_stress": {
            "overall_thermal_stress": "HIGH",
            "dominant_index": "WBGT",
            "indices": {},
            "explanation": []
        },
        "estimated_health_risk": {
            "risk_level": "HIGH",
            "dominant_driver": "WBGT",
            "explanation": []
        },
        "heatwave_outlook": {
            "status": "WATCH",
            "explanation": []
        }
    }
    
    risk = ConsolidatedRiskResponse(**risk_data)
    fc = service.generate_feature_collection([risk])
    
    assert fc.gis_data_status == "CONFIGURED"
    assert len(fc.features) > 0
    assert fc.features[0].geometry is not None
    assert fc.features[0].properties.geographic_id.startswith("W-")


def test_valid_geojson_serialization():
    service = SpatialRiskService()
    
    risk_data = {
        "location": {"lat": 9.965261, "lon": 76.248245},
        "timestamp": "2023-01-01T12:00:00Z",
        "thermal_stress": {
            "overall_thermal_stress": "HIGH",
            "dominant_index": "WBGT",
            "indices": {},
            "explanation": []
        },
        "estimated_health_risk": {
            "risk_level": "HIGH",
            "dominant_driver": "WBGT",
            "explanation": []
        },
        "heatwave_outlook": {
            "status": "WATCH",
            "explanation": []
        }
    }
    risk = ConsolidatedRiskResponse(**risk_data)
    fc = service.generate_feature_collection([risk])
    
    json_str = fc.model_dump_json()
    parsed = json.loads(json_str)
    
    assert parsed["type"] == "FeatureCollection"
    assert "features" in parsed
    assert len(parsed["features"]) > 0
    assert parsed["features"][0]["type"] == "Feature"
    assert "properties" in parsed["features"][0]
