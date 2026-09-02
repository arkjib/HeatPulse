import pytest
from app.gis.ward_mapping import WardMappingService

def test_load_all_kochi_wards():
    service = WardMappingService()
    wards = service.get_all_wards_with_centroids()
    
    assert len(wards) > 0
    # The requirement specifically mentions 71 named Kochi wards
    assert len(wards) == 71
    
    first_ward = wards[0]
    assert "ward_no" in first_ward
    assert "ward_name" in first_ward
    assert "latitude" in first_ward
    assert "longitude" in first_ward
    
    # Check bounds approximately around Kochi
    assert 9.0 <= first_ward["latitude"] <= 10.5
    assert 76.0 <= first_ward["longitude"] <= 77.0
