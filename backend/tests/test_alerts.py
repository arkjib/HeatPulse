import pytest
from app.alerts.action_engine import ActionEngine
from app.alerts.notification_service import NotificationService, NotificationProvider
from app.schemas.alerts import AlertPayload
from app.schemas.gis import GISFeatureCollection, GISFeature, GISFeatureProperties
from app.core.config import settings

class MockProvider(NotificationProvider):
    def __init__(self):
        self.sent_count = 0
    def send(self, alert: AlertPayload) -> bool:
        self.sent_count += 1
        return True


@pytest.fixture
def action_engine():
    return ActionEngine()


def _make_collection(ward_id, category, score, start_time):
    return GISFeatureCollection(
        gis_data_status="BOUNDARIES_NOT_CONFIGURED",
        features=[
            GISFeature(
                properties=GISFeatureProperties(
                    geographic_id=ward_id,
                    name="Ward",
                    geographic_level="WARD",
                    risk_score=score,
                    risk_category=category,
                    hazard_score=50,
                    timestamp=start_time,
                    forecast_horizon=0,
                    data_quality="COMPLETE"
                ),
                geometry=None
            )
        ]
    )

def test_deduplication_same_event(action_engine):
    c1 = _make_collection("W1", "HIGH", 55.0, "2023-01-01T12:00:00Z")
    
    # First generate should return 1 alert
    alerts1 = action_engine.generate_alerts(c1, "2023-01-01T12:00:00Z", "2023-01-01T15:00:00Z")
    assert len(alerts1) == 1
    
    # Second generate for EXACT SAME event should return 0 (deduplicated)
    alerts2 = action_engine.generate_alerts(c1, "2023-01-01T12:00:00Z", "2023-01-01T15:00:00Z")
    assert len(alerts2) == 0


def test_severity_change_generates_new_alert(action_engine):
    c1 = _make_collection("W1", "HIGH", 55.0, "2023-01-01T12:00:00Z")
    alerts1 = action_engine.generate_alerts(c1, "2023-01-01T12:00:00Z", "2023-01-01T15:00:00Z")
    assert len(alerts1) == 1
    
    # Category increases to EXTREME for the same period
    c2 = _make_collection("W1", "EXTREME", 85.0, "2023-01-01T12:00:00Z")
    alerts2 = action_engine.generate_alerts(c2, "2023-01-01T12:00:00Z", "2023-01-01T15:00:00Z")
    
    # Must generate a new alert because rule/category changed
    assert len(alerts2) == 1
    assert alerts2[0].alert_category == "EXTREME"


def test_non_overlapping_forecast_new_alert(action_engine):
    c1 = _make_collection("W1", "HIGH", 55.0, "2023-01-01T12:00:00Z")
    alerts1 = action_engine.generate_alerts(c1, "2023-01-01T12:00:00Z", "2023-01-01T15:00:00Z")
    assert len(alerts1) == 1
    
    # Next day
    alerts2 = action_engine.generate_alerts(c1, "2023-01-02T12:00:00Z", "2023-01-02T15:00:00Z")
    assert len(alerts2) == 1


def test_notification_disabled_prevents_sending():
    settings.NOTIFICATION_ENABLED = False
    provider = MockProvider()
    svc = NotificationService(providers=[provider])
    
    payload = AlertPayload(
        fingerprint="test", geographic_level="WARD", geographic_id="W1",
        alert_category="HIGH", rule_id="RULE_1", forecast_start="t1", forecast_end="t2",
        recommended_actions=[], alert_message="test"
    )
    
    res = svc.dispatch(payload)
    assert res.alert_lifecycle == "PENDING"
    assert provider.sent_count == 0


def test_notification_enabled_sends():
    settings.NOTIFICATION_ENABLED = True
    provider = MockProvider()
    svc = NotificationService(providers=[provider])
    
    payload = AlertPayload(
        fingerprint="test", geographic_level="WARD", geographic_id="W1",
        alert_category="HIGH", rule_id="RULE_1", forecast_start="t1", forecast_end="t2",
        recommended_actions=[], alert_message="test"
    )
    
    res = svc.dispatch(payload)
    assert res.alert_lifecycle == "SENT"
    assert provider.sent_count == 1
    settings.NOTIFICATION_ENABLED = False # revert
