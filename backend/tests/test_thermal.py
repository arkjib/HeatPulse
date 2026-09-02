import pytest
import math
from datetime import datetime, timezone
from app.thermal.heat_index import calculate_heat_index
from app.thermal.wbgt import calculate_wbgt
from app.thermal.utci import calculate_utci
from app.thermal.radiant_temperature import calculate_mrt
from app.thermal.validation import validate_thermal_inputs

def test_validation():
    assert validate_thermal_inputs(30.0, 50.0, 2.0) is True
    with pytest.raises(ValueError):
        validate_thermal_inputs(30.0, -10.0, 2.0)
    with pytest.raises(ValueError):
        validate_thermal_inputs(30.0, 50.0, -2.0)

# HEAT INDEX TESTS
def test_hi_non_applicable():
    res = calculate_heat_index(25.0, 50.0) # 77F < 80F
    assert res["status"] == "NOT_APPLICABLE"
    assert res["value_c"] is None

def test_hi_invalid():
    res = calculate_heat_index(30.0, 110.0)
    assert res["status"] == "INVALID_INPUT"

def test_hi_standard():
    # Benchmark from NWS Heat Index Calculator:
    # 86F (30.0C), 70% RH -> 95F (35.0C)
    res = calculate_heat_index(30.0, 70.0)
    assert res["status"] == "CALCULATED"
    assert round(res["value_c"], 1) == 35.0

# WBGT TESTS
def test_wbgt_invalid():
    dt = datetime(2023, 7, 15, 12, 0, tzinfo=timezone.utc)
    res = calculate_wbgt(30.0, -10.0, 2.0, 0.0, 28.6, 77.2, dt)
    assert res["status"] == "INVALID_INPUT"

def test_wbgt_night_vs_day():
    # Liljegren solver explicitly uses location and time
    dt_day = datetime(2023, 7, 15, 6, 0, tzinfo=timezone.utc)
    dt_night = datetime(2023, 7, 15, 20, 0, tzinfo=timezone.utc)
    day = calculate_wbgt(30.0, 50.0, 2.0, 800.0, 28.6, 77.2, dt_day)
    night = calculate_wbgt(30.0, 50.0, 2.0, 0.0, 28.6, 77.2, dt_night)
    assert day["status"] == "CALCULATED"
    assert night["status"] == "CALCULATED"
    assert day["value_c"] > night["value_c"]
    
    # INDEPENDENT REFERENCE VALIDATION:
    # Use pythermalcomfort ISO 7243 implementation as the independent reference
    # to verify that our final WBGT combination of Tnwb and Tg matches the standard.
    from pythermalcomfort.models import wbgt
    # For day case:
    tnwb = day["tnwb_c"]
    tg = day["tg_c"]
    ta = 30.0
    ref_wbgt = wbgt(tnwb, tg, ta, with_solar_load=True)
    
    # Compare
    assert round(day["value_c"], 1) == round(float(ref_wbgt.wbgt), 1)

# UTCI TESTS
def test_utci_domain_validation():
    res1 = calculate_utci(55.0, 50.0, 2.0, 55.0)
    assert res1["status"] == "NOT_APPLICABLE"
    res2 = calculate_utci(30.0, 50.0, 20.0, 30.0)
    assert res2["status"] == "NOT_APPLICABLE"

def test_utci_standard():
    res = calculate_utci(30.0, 50.0, 2.0, 30.0)
    assert res["status"] == "CALCULATED"
    assert res["value_c"] is not None

def test_utci_mrt_handling():
    res_shade = calculate_utci(30.0, 50.0, 2.0, 30.0)
    res_sun = calculate_utci(30.0, 50.0, 2.0, 50.0)
    assert res_sun["value_c"] > res_shade["value_c"]

# MRT TESTS
def test_mrt_invalid():
    dt = datetime(2023, 10, 10, 12, 0, tzinfo=timezone.utc)
    res = calculate_mrt(30.0, -100.0, 0.0, 0.0, 0.0, 28.6, 77.2, dt)
    assert res["status"] == "INVALID_INPUT"
    
def test_mrt_day_night():
    dt_day = datetime(2023, 6, 21, 12, 0, tzinfo=timezone.utc)
    dt_night = datetime(2023, 6, 21, 23, 0, tzinfo=timezone.utc)
    
    day = calculate_mrt(30.0, 800.0, 600.0, 200.0, 800.0, 28.6, 77.2, dt_day)
    night = calculate_mrt(30.0, 0.0, 0.0, 0.0, 0.0, 28.6, 77.2, dt_night)
    
    assert day["value_c"] > night["value_c"]
    assert night["value_c"] == 30.0
