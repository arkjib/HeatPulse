import pytest
from app.models.health_risk_model import HealthRiskModel
from app.schemas.risk import ConsolidatedRiskResponse

@pytest.fixture
def risk_model():
    return HealthRiskModel()

def test_dominant_index_selection(risk_model):
    wbgt_data = {"value_c": 31.5, "status": "CALCULATED", "method": "Physics"} # HIGH severity (3)
    utci_data = {"value_c": 50.0, "status": "CALCULATED", "method": "Physics"} # EXTREME severity (4)
    hi_data = {"value_c": 30.0, "status": "CALCULATED", "method": "Physics"} # SAFE/CAUTION (1)

    res = risk_model.compute_risk(
        lat=9.9, lon=76.2, timestamp="2023-01-01T12:00:00Z",
        wbgt_data=wbgt_data, utci_data=utci_data, hi_data=hi_data, max_temp_c=36.0
    )
    
    assert res.thermal_stress.dominant_index == "utci"
    assert res.thermal_stress.overall_thermal_stress == "EXTREME"
    assert res.estimated_health_risk.risk_level == "EXTREME"
    assert res.estimated_health_risk.dominant_driver == "UTCI"
    assert res.heatwave_outlook.status == "WATCH"


def test_heat_index_not_applicable(risk_model):
    wbgt_data = {"value_c": 28.0, "status": "CALCULATED", "method": "Physics"}
    utci_data = {"value_c": 28.0, "status": "CALCULATED", "method": "Physics"}
    hi_data = {"value_c": 28.0, "status": "CALCULATED", "method": "Physics"} # Should be marked N/A

    res = risk_model.compute_risk(
        lat=9.9, lon=76.2, timestamp="2023-01-01T12:00:00Z",
        wbgt_data=wbgt_data, utci_data=utci_data, hi_data=hi_data, max_temp_c=25.0
    )
    
    assert res.thermal_stress.indices["hi"].status == "NOT_APPLICABLE"
    assert res.thermal_stress.indices["hi"].value is None


def test_heatwave_outlook_imd_criteria(risk_model):
    wbgt_data = {"value_c": 30.0, "status": "CALCULATED", "method": "Physics"}
    utci_data = {"value_c": 30.0, "status": "CALCULATED", "method": "Physics"}
    hi_data = {"value_c": 30.0, "status": "CALCULATED", "method": "Physics"}

    # Heatwave WATCH (>=35C)
    res_watch = risk_model.compute_risk(
        lat=9.9, lon=76.2, timestamp="2023-01-01T12:00:00Z",
        wbgt_data=wbgt_data, utci_data=utci_data, hi_data=hi_data, max_temp_c=35.5
    )
    assert res_watch.heatwave_outlook.status == "WATCH"

    # Heatwave ACTIVE (>=37C)
    res_active = risk_model.compute_risk(
        lat=9.9, lon=76.2, timestamp="2023-01-01T12:00:00Z",
        wbgt_data=wbgt_data, utci_data=utci_data, hi_data=hi_data, max_temp_c=37.5
    )
    assert res_active.heatwave_outlook.status == "ACTIVE"
