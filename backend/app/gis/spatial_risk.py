from typing import List, Dict, Any
from app.schemas.risk import ConsolidatedRiskResponse
from app.schemas.gis import GISFeature, GISFeatureProperties, GISFeatureCollection
from app.gis.ward_mapping import WardMappingService

class SpatialRiskService:
    def __init__(self):
        self.ward_mapping = WardMappingService()

    def generate_feature_collection(self, risk_responses: List[ConsolidatedRiskResponse], horizon: int = 0) -> GISFeatureCollection:
        features = []
        
        for risk in risk_responses:
            # For each risk response (computed at a lat/lon), figure out the geographic units.
            # In a real system, we'd do a point-in-polygon spatial join here.
            # Since boundaries are unavailable, we use the fallback from WardMappingService.
            units = self.ward_mapping.get_mock_wards_for_location(risk.location["lat"], risk.location["lon"])
            
            for unit in units:
                geom = self.ward_mapping.get_geometry(unit["geographic_id"], unit["geographic_level"])
                
                props = GISFeatureProperties(
                    geographic_id=unit["geographic_id"],
                    name=unit["name"],
                    geographic_level=unit["geographic_level"],
                    risk_score=0.0, # Removed numeric score
                    risk_category=risk.estimated_health_risk.risk_level,
                    hazard_score=0.0,
                    exposure_score=0.0,
                    vulnerability_score=0.0,
                    timestamp=risk.timestamp,
                    forecast_horizon=horizon,
                    data_quality="COMPLETE"
                )
                
                features.append(GISFeature(properties=props, geometry=geom))
                
        # Also could aggregate to ZONE and CITY levels here based on wards
        # But we only have one mock point.

        return GISFeatureCollection(
            features=features,
            gis_data_status=self.ward_mapping.get_boundary_status()
        )
