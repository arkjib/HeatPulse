import json
import os
from typing import Optional
from app.gis.ward_mapping import WardMappingService

class HealthDataService:
    def __init__(self):
        self.ward_mapping = WardMappingService()
        self.data_by_ward = {}
        
        data_path = os.path.join(os.path.dirname(__file__), "../../../data/health_indicators.json")
        try:
            with open(data_path, "r") as f:
                data = json.load(f)
                for item in data:
                    self.data_by_ward[item["ward_id"]] = item
        except Exception as e:
            print(f"Error loading health_indicators.json: {e}")

    def get_health_outcome_status(self) -> str:
        """
        Since we have KCH data, we can return something meaningful.
        """
        return "VALIDATED_WITH_LOCAL_DATA" if self.data_by_ward else "NOT_VALIDATED"

    def get_health_data_available(self, lat: float, lon: float, timestamp: str) -> bool:
        """
        Checks if real health data is available for a given location and time.
        """
        wards = self.ward_mapping.get_mock_wards_for_location(lat, lon)
        if wards:
            wid = wards[0]["geographic_id"]
            if wid in self.data_by_ward:
                return True
        return False
        
    def get_health_indicators(self, lat: float, lon: float) -> Optional[dict]:
        wards = self.ward_mapping.get_mock_wards_for_location(lat, lon)
        if wards:
            wid = wards[0]["geographic_id"]
            return self.data_by_ward.get(wid)
        return None
