import logging
from typing import Any

from app.providers.base import BaseProvider


logger = logging.getLogger(__name__)


class TeamsProvider(BaseProvider):
    async def dispatch(self, event: dict[str, Any]) -> dict[str, Any]:
        logger.info("[MOCK] Teams dispatch acionado para parceiro=%s", event.get("partner"))
        return {
            "provider": self.name,
            "status": "mock_dispatched",
            "event_type": event.get("event_type"),
        }

    async def cancel(self, payload: dict[str, Any]) -> dict[str, Any]:
        logger.info("[MOCK] Teams cancel acionado para id=%s", payload.get("dispatch_id"))
        return {"provider": self.name, "status": "mock_canceled"}
