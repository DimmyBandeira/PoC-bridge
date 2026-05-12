import base64
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

from app.core.iconvnet_auth import build_iconvnet_auth_headers


logger = logging.getLogger(__name__)


class IconvnetAiEventProvider:
    def __init__(self, name: str, config: dict[str, Any], timeout_seconds: float = 8.0) -> None:
        self.name = name
        self.config = config
        self._client = httpx.AsyncClient(timeout=timeout_seconds)
        self._max_bytes = int(config.get("max_image_size_bytes", 2 * 1024 * 1024))

    async def dispatch_photo_base64(self, photo_path: str, alarm_name: str | None, dev_name: str | None) -> dict[str, Any]:
        logger.info("iconvnet_ai_event_start mode=base64 provider=%s", self.name)
        file_path = Path(photo_path)
        if not file_path.exists():
            return {"provider": self.name, "status": "ai_event_file_not_found", "ok": False, "message": "Arquivo de imagem não encontrado."}
        if file_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
            return {"provider": self.name, "status": "ai_event_invalid_extension", "ok": False, "message": "Extensão de imagem inválida."}
        file_size = file_path.stat().st_size
        if file_size > self._max_bytes:
            return {"provider": self.name, "status": "ai_event_image_too_large", "ok": False, "message": "Imagem excede limite configurado para teste."}
        encoded = base64.b64encode(file_path.read_bytes()).decode("utf-8")
        payload = self._build_ai_payload(encoded, alarm_name, dev_name)
        logger.info("iconvnet_ai_event_payload_ready has_img=%s has_big_img=%s base64_size=%s", True, True, len(encoded))
        return await self._post_ai_event(payload)

    async def dispatch_photo_url(self, image_url: str, alarm_name: str | None, dev_name: str | None) -> dict[str, Any]:
        logger.info("iconvnet_ai_event_start mode=url provider=%s", self.name)
        if not image_url.strip():
            return {"provider": self.name, "status": "ai_event_image_url_required", "ok": False, "message": "image_url é obrigatório."}
        payload = self._build_ai_payload(image_url.strip(), alarm_name, dev_name)
        logger.info("iconvnet_ai_event_payload_ready has_img=%s has_big_img=%s base64_size=%s", True, True, 0)
        return await self._post_ai_event(payload)

    def _build_ai_payload(self, image_value: str, alarm_name: str | None, dev_name: str | None) -> dict[str, Any]:
        return {
            "uid": "all",
            "targetRect": "",
            "alarmName": alarm_name or "WebGuardiao Alert",
            "alarmType": "webguardiao_photo_test",
            "devName": dev_name or "PoC Bridge",
            "alarmTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "bigImg": image_value,
            "img": image_value,
        }

    async def _post_ai_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        endpoint = self.config.get("ai_event_endpoint", "")
        if not endpoint:
            return {"provider": self.name, "status": "ai_event_endpoint_missing", "ok": False, "message": "ai_event_endpoint não configurado."}
        headers = build_iconvnet_auth_headers(self.config)
        try:
            response = await self._client.post(endpoint, headers=headers, data={"data": json.dumps(payload, ensure_ascii=False)})
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.exception("Falha HTTP no iconvnet_ai_event")
            return {"provider": self.name, "status": "provider_http_error", "ok": False, "message": str(exc)}
        try:
            data = response.json()
        except ValueError:
            return {"provider": self.name, "status": "invalid_provider_response", "ok": False, "message": "Resposta não-JSON do provider."}
        code = data.get("code")
        ok = code == 0
        logger.info("iconvnet_ai_event_response code=%s ok=%s", code, ok)
        return {"provider": self.name, "status": "dispatched" if ok else "provider_rejected", "ok": ok, "code": code, "message": data.get("message"), "raw": data}

    async def close(self) -> None:
        await self._client.aclose()
