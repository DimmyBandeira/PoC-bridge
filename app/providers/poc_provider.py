import logging
from typing import Any

import httpx

from app.core.security import generate_sign, get_current_timestamp
from app.providers.base import BaseProvider


logger = logging.getLogger(__name__)


class PoCProvider(BaseProvider):
    def __init__(self, name: str, config: dict[str, Any], timeout_seconds: float = 8.0) -> None:
        super().__init__(name=name, config=config)
        self._client = httpx.AsyncClient(timeout=timeout_seconds)

    async def dispatch(self, event: dict[str, Any]) -> dict[str, Any]:
        if not self.config.get("enabled", True):
            logger.info("PoCProvider desabilitado em configuração. Usando mock local.")
            return {
                "provider": self.name,
                "status": "disabled_mock",
                "broad_id": f"mock-{event.get('event_type', 'event')}",
            }

        timestamp = get_current_timestamp()
        app_key = self.config.get("appKey", "")
        app_secret = self.config.get("appSecret", "")
        sign = generate_sign(app_key=app_key, app_secret=app_secret, timestamp=timestamp)

        endpoint = self.config.get("dispatch_endpoint", "")
        if not endpoint:
            raise ValueError("dispatch_endpoint não configurado para PoCProvider")

        body = {
            "appKey": app_key,
            "time": timestamp,
            "sign": sign,
            "content": event.get("content", ""),
            "member": event.get("member", "all"),
            "brd_hz": event.get("brd_hz", 2),
        }

        if event.get("photo_path"):
            body["photo_path"] = event["photo_path"]
            body["text"] = event.get("text", "")

        try:
            response = await self._client.post(endpoint, json=body)
            response.raise_for_status()
            data = response.json()
            return {
                "provider": self.name,
                "status": "dispatched",
                "raw": data,
                "broad_id": data.get("broad_id") or data.get("id") or "unknown",
            }
        except httpx.HTTPError:
            logger.exception("Falha de integração no PoCProvider dispatch")
            raise

    async def cancel(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.config.get("enabled", True):
            return {"provider": self.name, "status": "disabled_mock_canceled"}

        endpoint = self.config.get("cancel_endpoint", "")
        if not endpoint:
            raise ValueError("cancel_endpoint não configurado para PoCProvider")

        timestamp = get_current_timestamp()
        app_key = self.config.get("appKey", "")
        app_secret = self.config.get("appSecret", "")
        sign = generate_sign(app_key=app_key, app_secret=app_secret, timestamp=timestamp)

        body = {
            "appKey": app_key,
            "time": timestamp,
            "sign": sign,
            "broad_id": payload.get("dispatch_id") or payload.get("broad_id"),
        }

        try:
            response = await self._client.post(endpoint, json=body)
            response.raise_for_status()
            return {
                "provider": self.name,
                "status": "canceled",
                "raw": response.json(),
            }
        except httpx.HTTPError:
            logger.exception("Falha de integração no PoCProvider cancel")
            raise

    async def close(self) -> None:
        await self._client.aclose()
