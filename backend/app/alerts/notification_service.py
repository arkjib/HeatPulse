from abc import ABC, abstractmethod
from typing import List
from app.core.config import settings
from app.schemas.alerts import AlertPayload
import logging

logger = logging.getLogger(__name__)

class NotificationProvider(ABC):
    @abstractmethod
    def send(self, alert: AlertPayload) -> bool:
        pass


class SMSProvider(NotificationProvider):
    def send(self, alert: AlertPayload) -> bool:
        # In a real system, this interacts with Twilio/AWS SNS etc.
        logger.info(f"Mock SMS Provider sending: {alert.alert_message}")
        return True


class WhatsAppProvider(NotificationProvider):
    def send(self, alert: AlertPayload) -> bool:
        logger.info(f"Mock WhatsApp Provider sending: {alert.alert_message}")
        return True


class NotificationService:
    def __init__(self, providers: List[NotificationProvider] = None):
        self.providers = providers or []

    def dispatch(self, payload: AlertPayload) -> AlertPayload:
        if not settings.NOTIFICATION_ENABLED:
            logger.info(f"Notification dispatch skipped (disabled). Fingerprint: {payload.fingerprint}")
            payload.alert_lifecycle = "PENDING"
            return payload

        if not self.providers:
            logger.error("Notification enabled but no providers configured.")
            payload.alert_lifecycle = "FAILED"
            return payload

        success = True
        for provider in self.providers:
            try:
                res = provider.send(payload)
                if not res: success = False
            except Exception as e:
                logger.error(f"Provider error: {e}")
                success = False

        if success:
            payload.alert_lifecycle = "SENT"
        else:
            payload.alert_lifecycle = "FAILED"

        return payload
