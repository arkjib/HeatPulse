import hashlib
from typing import List, Dict, Tuple
from app.schemas.gis import GISFeatureCollection
from app.schemas.alerts import AlertPayload
from app.alerts.alert_rules import get_rule_for_category

class ActionEngine:
    def __init__(self):
        self.state_cache = {}

    def _generate_fingerprint(self, geographic_level: str, geographic_id: str, alert_category: str,
                              forecast_start: str, forecast_end: str, rule_id: str) -> str:
        payload = f"{geographic_level}:{geographic_id}:{alert_category}:{forecast_start}:{forecast_end}:{rule_id}"
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()

    def generate_alerts(self, collection: GISFeatureCollection, forecast_start: str, forecast_end: str) -> List[AlertPayload]:
        alerts = []
        for feature in collection.features:
            props = feature.properties
            
            # Identify the appropriate rule based on the risk category
            rule = get_rule_for_category(props.risk_category)
            
            # Deduplication fingerprint (as required by the prompt)
            fingerprint = self._generate_fingerprint(
                geographic_level=props.geographic_level,
                geographic_id=props.geographic_id,
                alert_category=props.risk_category,
                forecast_start=forecast_start,
                forecast_end=forecast_end,
                rule_id=rule.rule_id
            )
            
            # Check deduplication
            if fingerprint in self.state_cache:
                continue
                
            actions = [r.action_id for r in rule.recommended_actions]
            
            message = (f"{props.risk_category} HEAT RISK\nArea: {props.name}\n"
                       f"Duration: {forecast_start} - {forecast_end}\n"
                       f"Actions: {', '.join(actions)}")
                       
            alert = AlertPayload(
                fingerprint=fingerprint,
                geographic_level=props.geographic_level,
                geographic_id=props.geographic_id,
                alert_category=props.risk_category,
                rule_id=rule.rule_id,
                forecast_start=forecast_start,
                forecast_end=forecast_end,
                risk_score=props.risk_score,
                recommended_actions=actions,
                alert_message=message
            )
            
            alerts.append(alert)
            # Store in cache for deduplication
            self.state_cache[fingerprint] = True
            
        return alerts
