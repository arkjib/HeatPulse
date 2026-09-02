import json
import os
from typing import Optional
from app.core.config import settings
from app.schemas.risk import RiskComponent
from app.gis.ward_mapping import WardMappingService

class DemographicService:
    def __init__(self):
        self.demo_enabled = settings.DEMO_DATA_ENABLED
        self.ward_mapping = WardMappingService()
        self.data_by_ward = {}
        
        data_path = os.path.join(os.path.dirname(__file__), "../../../data/demographics.json")
        try:
            with open(data_path, "r") as f:
                data = json.load(f)
                for item in data:
                    self.data_by_ward[item["ward_id"]] = item
        except Exception as e:
            print(f"Error loading demographics.json: {e}")
            
        self.max_pop = max([d.get("population", 1) for d in self.data_by_ward.values()] + [1])
        self.max_pop_dens = max([d.get("pop_density_per_ha", 1) for d in self.data_by_ward.values()] + [1])

    def _get_missing_component(self) -> RiskComponent:
        return RiskComponent(
            raw_value=None,
            unit=None,
            normalized_value=None,
            source="UNAVAILABLE",
            status="MISSING",
            geographic_level="OTHER",
            is_real_data=True,
        )
        
    def _get_demo_component(self, raw_val: float, unit: str, norm_val: float) -> RiskComponent:
        return RiskComponent(
            raw_value=raw_val,
            unit=unit,
            normalized_value=norm_val,
            source="DEMO_PROFILE",
            status="ESTIMATED",
            geographic_level="WARD",
            is_real_data=False,
        )

    def _get_real_component(self, raw_val: float, unit: str, norm_val: float) -> RiskComponent:
        return RiskComponent(
            raw_value=raw_val,
            unit=unit,
            normalized_value=max(0.0, min(100.0, norm_val)),
            source="Kochi_Demographics_JSON",
            status="AVAILABLE",
            geographic_level="WARD",
            is_real_data=True,
        )

    def _get_ward_data(self, lat: float, lon: float):
        wards = self.ward_mapping.get_mock_wards_for_location(lat, lon)
        if wards:
            wid = wards[0]["geographic_id"]
            return self.data_by_ward.get(wid)
        return None

    def get_population(self, lat: float, lon: float) -> RiskComponent:
        ward_data = self._get_ward_data(lat, lon)
        if ward_data:
            val = ward_data["population"]
            return self._get_real_component(val, "people", (val / self.max_pop) * 100)
        if self.demo_enabled:
            return self._get_demo_component(50000, "people", 60.0)
        return self._get_missing_component()

    def get_population_density(self, lat: float, lon: float) -> RiskComponent:
        ward_data = self._get_ward_data(lat, lon)
        if ward_data:
            val = ward_data["pop_density_per_ha"]
            return self._get_real_component(val, "people/ha", (val / self.max_pop_dens) * 100)
        if self.demo_enabled:
            return self._get_demo_component(12000, "people/km2", 75.0)
        return self._get_missing_component()

    def get_elderly_percentage(self, lat: float, lon: float) -> RiskComponent:
        ward_data = self._get_ward_data(lat, lon)
        if ward_data:
            val = ward_data["elderly_share_pct"]
            return self._get_real_component(val, "percent", (val / 30.0) * 100) # Assuming 30% is very high
        if self.demo_enabled:
            return self._get_demo_component(14.2, "percent", 62.0)
        return self._get_missing_component()

    def get_outdoor_worker_percentage(self, lat: float, lon: float) -> RiskComponent:
        ward_data = self._get_ward_data(lat, lon)
        if ward_data:
            val = ward_data["outdoor_worker_share_pct"]
            return self._get_real_component(val, "percent", (val / 80.0) * 100) # Assuming 80% is max
        if self.demo_enabled:
            return self._get_demo_component(25.0, "percent", 80.0)
        return self._get_missing_component()

    def get_local_vulnerability(self, lat: float, lon: float) -> RiskComponent:
        ward_data = self._get_ward_data(lat, lon)
        if ward_data:
            access = ward_data["healthcare_access_index"]
            # Lower healthcare access means higher vulnerability
            vuln_score = max(0.0, 100.0 - access)
            return self._get_real_component(vuln_score / 100.0, "index", vuln_score)
        if self.demo_enabled:
            return self._get_demo_component(0.65, "index", 65.0)
        return self._get_missing_component()
