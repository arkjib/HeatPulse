from typing import Dict, Any
from app.schemas.predict import RiskResponse

# Configurable thresholds
RISK_THRESHOLDS = {
    "wbgt": [
        {"max": 27.7, "category": "LOW", "desc": "Minimal heat stress", "severity": 0},
        {"max": 29.4, "category": "MODERATE", "desc": "Caution: fluid intake recommended", "severity": 1},
        {"max": 31.0, "category": "HIGH", "desc": "Extreme caution: limit strenuous outdoor activity", "severity": 2},
        {"max": 32.1, "category": "VERY_HIGH", "desc": "Danger: modify work/rest schedules", "severity": 3},
        {"max": 999.0, "category": "EXTREME", "desc": "Extreme danger: cancel non-essential outdoor work", "severity": 4}
    ],
    "utci": [
        {"max": 9.0, "category": "COLD_STRESS", "desc": "Cold stress possible", "severity": 0},
        {"max": 26.0, "category": "NO_THERMAL_STRESS", "desc": "Comfortable", "severity": 0},
        {"max": 32.0, "category": "MODERATE", "desc": "Moderate heat stress", "severity": 1},
        {"max": 38.0, "category": "STRONG", "desc": "Strong heat stress", "severity": 2},
        {"max": 46.0, "category": "VERY_STRONG", "desc": "Very strong heat stress", "severity": 3},
        {"max": 999.0, "category": "EXTREME", "desc": "Extreme heat stress", "severity": 4}
    ],
    "hi": [
        {"max": 27.0, "category": "SAFE", "desc": "Normal conditions", "severity": 0},
        {"max": 32.0, "category": "CAUTION", "desc": "Fatigue possible with prolonged exposure", "severity": 1},
        {"max": 41.0, "category": "EXTREME_CAUTION", "desc": "Heat cramps and heat exhaustion possible", "severity": 2},
        {"max": 54.0, "category": "DANGER", "desc": "Heat cramps/exhaustion likely; heatstroke possible", "severity": 3},
        {"max": 999.0, "category": "EXTREME_DANGER", "desc": "Heatstroke highly likely", "severity": 4}
    ]
}

def classify_risk(index_name: str, value: float) -> RiskResponse:
    thresholds = RISK_THRESHOLDS.get(index_name, [])
    for t in thresholds:
        if value < t["max"]:
            return RiskResponse(category=t["category"], description=t["desc"])
    
    return RiskResponse(category="UNKNOWN", description="No risk classification available")
