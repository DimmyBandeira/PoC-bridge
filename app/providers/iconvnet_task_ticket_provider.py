import base64
import logging
from typing import Any

import httpx

from app.core.iconvnet_auth import build_iconvnet_auth_headers
from app.core.security import get_current_timestamp


logger = logging.getLogger(__name__)


class IconvnetTaskTicketProvider:
    def __init__(self, name: str, config: dict[str, Any], timeout_seconds: float = 8.0) -> None:
        self.name = name
        self.config = config
        self._client = httpx.AsyncClient(timeout=timeout_seconds)
        self._closed = False

    async def create_ticket(
        self,
        title: str,
        notes: str,
        uid: str | int | None,
        image_urls: list[str] | None,
        video_urls: list[str] | None,
    ) -> dict[str, Any]:
        image_urls = image_urls or []
        video_urls = video_urls or []
        logger.info("iconvnet_task_ticket_start image_count=%s video_count=%s", len(image_urls), len(video_urls))
        if not image_urls and not video_urls:
            return {"provider": self.name, "status": "task_ticket_media_required", "ok": False, "message": "Informe image_urls ou video_urls."}
        resolved_uid = str(uid or self.config.get("default_uid") or "").strip()
        if not resolved_uid:
            return {"provider": self.name, "status": "task_ticket_uid_required", "ok": False, "message": "UID é obrigatório para task ticket."}
        endpoint = self.config.get("task_ticket_endpoint", "")
        if not endpoint:
            return {"provider": self.name, "status": "task_ticket_endpoint_missing", "ok": False, "message": "task_ticket_endpoint não configurado."}
        begin_time = get_current_timestamp()
        end_time = begin_time + 3600
        form_data: list[tuple[str, str]] = [
            ("title", base64.b64encode(title.encode("utf-8")).decode("utf-8")),
            ("notes", base64.b64encode(notes.encode("utf-8")).decode("utf-8")),
            ("level", "1"),
            ("begintime", str(begin_time)),
            ("endtime", str(end_time)),
            ("uid", resolved_uid),
        ]
        for image_url in image_urls:
            if image_url.strip():
                form_data.append(("image[]", image_url.strip()))
        for video_url in video_urls:
            if video_url.strip():
                form_data.append(("video[]", video_url.strip()))
        headers = build_iconvnet_auth_headers(self.config)
        try:
            response = await self._client.post(endpoint, headers=headers, data=form_data)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.exception("Falha HTTP no iconvnet_task_ticket")
            return {"provider": self.name, "status": "provider_http_error", "ok": False, "message": str(exc)}
        try:
            data = response.json()
        except ValueError:
            return {"provider": self.name, "status": "invalid_provider_response", "ok": False, "message": "Resposta não-JSON do provider."}
        code = data.get("code")
        ok = code == 0
        logger.info("iconvnet_task_ticket_response code=%s ok=%s", code, ok)
        return {"provider": self.name, "status": "created" if ok else "provider_rejected", "ok": ok, "code": code, "message": data.get("message"), "raw": data}

    async def close(self) -> None:
        if self._closed or self._client.is_closed:
            return
        self._closed = True
        await self._client.aclose()
