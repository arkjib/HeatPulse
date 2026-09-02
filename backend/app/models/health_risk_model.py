from typing import Optional, List, Dict
from app.core.config import settings
from app.schemas.risk import (
    ThermalIndexRisk,
    ThermalStressResponse,
    EstimatedHealthRisk,
    HeatwaveOutlook,
    ConsolidatedRiskResponse
)
from app.data.demographic import DemographicService
from app.ml.risk_classifier import classify_risk, RISK_THRESHOLDS

class HealthRiskModel:
    def __init__(self):
        self.demographic = DemographicService()
        self.w_haz = settings.RISK_WEIGHT_HAZARD
        self.w_vul = settings.RISK_WEIGHT_VULNERABILITY
        self.w_exp = settings.RISK_WEIGHT_EXPOSURE

    def _get_severity(self, index_name: str, category: str) -> int:
        thresholds = RISK_THRESHOLDS.get(index_name, [])
        for t in thresholds:
            if t["category"] == category:
                return t.get("severity", 0)
        return 0

    def compute_risk(self, lat: float, lon: float, timestamp: str,
                     wbgt_data: dict, utci_data: dict, hi_data: dict, max_temp_c: Optional[float] = None) -> ConsolidatedRiskResponse:
        
        indices = {}
        
        # Classify each index
        for idx_name, data in [("wbgt", wbgt_data), ("utci", utci_data), ("hi", hi_data)]:
            val = data.get("value_c")
            status = data.get("status", "NOT_APPLICABLE")
            method = data.get("method", "Unknown")
            reason = data.get("reason")
            
            # Enforce Heat Index applicability if temperature is known
            if idx_name == "hi" and max_temp_c is not None and max_temp_c < 26.7:
                val = None
                status = "NOT_APPLICABLE"
                reason = "Heat Index is not applicable below 80°F (26.7°C)"
            
            if val is not None and status == "CALCULATED":
                classification = classify_risk(idx_name, val)
                cat = classification.category
                desc = classification.description
            else:
                cat = "UNKNOWN" if status != "NOT_APPLICABLE" else "NOT_APPLICABLE"
                desc = "No risk classification available" if status != "NOT_APPLICABLE" else "Index not applicable in these conditions"

            indices[idx_name] = ThermalIndexRisk(
                value=val,
                status=status,
                category=cat,
                description=desc,
                reason=reason,
                method=method
            )

        # Determine overall thermal stress based on dominant index (highest severity)
        max_severity = -1
        dominant = "wbgt"
        overall_cat = "LOW"
        
        for idx_name, res in indices.items():
            if res.status == "CALCULATED":
                sev = self._get_severity(idx_name, res.category)
                if sev > max_severity:
                    max_severity = sev
                    dominant = idx_name
                    overall_cat = res.category

        if max_severity == -1:
            overall_cat = "UNKNOWN"
            dominant = "None"
            explanation = ["No thermal indices could be calculated"]
        else:
            explanation = [f"Dominant thermal stress driver is {dominant.upper()} reaching {overall_cat} severity."]

        thermal_stress = ThermalStressResponse(
            overall_thermal_stress=overall_cat,
            dominant_index=dominant,
            indices=indices,
            explanation=explanation
        )

        # Vulnerability & Exposure
        elderly = self.demographic.get_elderly_percentage(lat, lon)
        worker = self.demographic.get_outdoor_worker_percentage(lat, lon)
        
        vul_factors = []
        if elderly.normalized_value and elderly.normalized_value > 50:
            vul_factors.append("High elderly population")
        if worker.normalized_value and worker.normalized_value > 50:
            vul_factors.append("High proportion of outdoor workers")
            
        health_cat = overall_cat
        if vul_factors and max_severity > 0:
            # If there's thermal stress and high vulnerability, we might elevate the text explanation
            explanation_health = ["Elevated risk due to: " + ", ".join(vul_factors)]
        else:
            explanation_health = ["Normal vulnerability profile for this area."]
            
        estimated_health_risk = EstimatedHealthRisk(
            risk_level=health_cat,
            dominant_driver=dominant.upper(),
            explanation=explanation_health
        )

        # Heatwave Outlook (IMD Coastal criterion: Max temp >= 37C)
        # Using a simplified criteria based on max temperature for Kochi
        hw_status = "NO_HEATWAVE"
        hw_exp = ["Current conditions do not meet IMD coastal heatwave criteria."]
        if max_temp_c is not None:
            if max_temp_c >= 37.0:
                hw_status = "ACTIVE"
                hw_exp = [f"Max temperature {max_temp_c}°C meets IMD coastal heatwave criteria (>= 37°C)"]
            elif max_temp_c >= 35.0:
                hw_status = "WATCH"
                hw_exp = [f"Max temperature {max_temp_c}°C is approaching heatwave threshold."]

        heatwave_outlook = HeatwaveOutlook(
            status=hw_status,
            explanation=hw_exp
        )

        return ConsolidatedRiskResponse(
            location={"lat": lat, "lon": lon},
            timestamp=str(timestamp),
            thermal_stress=thermal_stress,
            estimated_health_risk=estimated_health_risk,
            heatwave_outlook=heatwave_outlook
        )
