import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

from app.core.security import generate_sign, get_current_timestamp
from app.providers.base import BaseProvider


logger = logging.getLogger(__name__)


class PoCProvider(BaseProvider):
    def __init__(self, name: str, config: dict[str, Any], timeout_seconds: float = 8.0) -> None:
        super().__init__(name=name, config=config)
        self._client = httpx.AsyncClient(timeout=timeout_seconds)
        self._closed = False

    async def dispatch(self, event: dict[str, Any]) -> dict[str, Any]:
        if not self.config.get("enabled", True):
            logger.info("PoCProvider desabilitado em configuração. Usando mock local.")
            return {
                "provider": self.name,
                "status": "disabled_mock",
                "broad_id": f"mock-{event.get('event_type', 'event')}",
            }

        endpoint = self.config.get("dispatch_endpoint", "")
        if not endpoint:
            raise ValueError("dispatch_endpoint não configurado para PoCProvider")

        logger.info(
            "poc_dispatch_start provider=%s event_type=%s has_photo=%s",
            self.name,
            event.get("event_type"),
            bool(event.get("photo_path")),
        )
        headers = self._build_auth_headers()
        if event.get("photo_path"):
            upload_result = await self._upload_photo_if_needed(event)
            if upload_result is not None:
                return upload_result
            form_data = self._build_photo_form(event, event["_remote_file_path"])
        else:
            form_data = self._build_text_form(event)

        logger.info(
            "poc_request_form_ready type=%s member=%s brd_hz=%s",
            form_data.get("type"),
            form_data.get("member"),
            form_data.get("brd_hz"),
        )

        try:
            response = await self._client.post(endpoint, headers=headers, data=form_data)
            response.raise_for_status()
            data = response.json()
            normalized = self._normalize_provider_response(data)
            logger.info(
                "poc_dispatch_response code=%s provider_status=%s",
                response.status_code,
                normalized.get("status"),
            )
            return {
                "provider": self.name,
                "status": normalized.get("status", "dispatched"),
                "raw": data,
                "broad_id": normalized.get("broad_id", "unknown"),
                "ok": normalized.get("ok", True),
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

        provider_broad_id = payload.get("provider_broad_id") or payload.get("dispatch_id") or payload.get("broad_id")
        logger.info("poc_cancel_start dispatch_id=%s provider_broad_id=%s", payload.get("dispatch_id"), provider_broad_id)
        if not provider_broad_id:
            return {
                "provider": self.name,
                "status": "cancel_broad_required",
                "ok": False,
                "message": "provider_broad_id ausente para cancelamento.",
            }
        headers = self._build_auth_headers()
        body = {"broad": provider_broad_id}

        try:
            response = await self._client.post(endpoint, headers=headers, data=body)
            response.raise_for_status()
            return {
                "provider": self.name,
                "status": "canceled",
                "raw": response.json(),
            }
        except httpx.HTTPError:
            logger.exception("Falha de integração no PoCProvider cancel")
            raise

    def _build_auth_headers(self) -> dict[str, str]:
        timestamp = get_current_timestamp()
        app_key = self.config.get("appKey", "")
        app_secret = self.config.get("appSecret", "")
        sign = generate_sign(app_key=app_key, app_secret=app_secret, timestamp=timestamp)
        headers = {"appKey": app_key, "time": str(timestamp), "sign": sign}
        logger.info("poc_auth_headers_built appKey_present=%s sign_present=%s", bool(app_key), bool(sign))
        return headers

    def _build_common_form(self, event: dict[str, Any]) -> dict[str, Any]:
        today = datetime.now().strftime("%Y-%m-%d")
        return {
            "member": event.get("member", "all"),
            "timezone": self.config.get("timezone", "America/Sao_Paulo"),
            "brd_hz": str(event.get("brd_hz", 1)),
            "startT": today,
            "endT": today,
            "wdays": str(event.get("wdays", "127")),
            "effect_time": str(event.get("effect_time", "00:00")),
        }

    def _build_text_form(self, event: dict[str, Any]) -> dict[str, Any]:
        form = self._build_common_form(event)
        form.update({"type": 0, "content": event.get("content", "").strip()})
        return form

    def _build_photo_form(self, event: dict[str, Any], remote_file_path: str) -> dict[str, Any]:
        form = self._build_common_form(event)
        text = (event.get("text") or event.get("content") or "").strip()
        form.update({"type": 2, "content": f"{remote_file_path}|{text}"})
        return form

    def _normalize_provider_response(self, data: dict[str, Any]) -> dict[str, Any]:
        nested_result = data.get("result", {}) if isinstance(data.get("result"), dict) else {}
        broad_id = data.get("broad_id") or data.get("id") or nested_result.get("broad_id") or nested_result.get("id")
        code = data.get("code")
        if code == 0:
            return {"status": "dispatched" if broad_id else "dispatched_without_broad_id", "ok": True, "broad_id": broad_id}
        return {"status": "provider_rejected", "ok": False, "broad_id": broad_id}

    async def _upload_photo_if_needed(self, event: dict[str, Any]) -> dict[str, Any] | None:
        photo_path = event.get("photo_path", "")
        if not photo_path:
            return None
        file_path = Path(photo_path)
        if not file_path.exists():
            return {"provider": self.name, "status": "photo_file_not_found", "ok": False, "message": "Arquivo de foto não encontrado."}
        ext = self._map_upload_ext(file_path.suffix.lower())
        logger.info("poc_photo_upload_start endpoint_configured=%s ext=%s", bool(self.config.get("upload_endpoint", "")), ext)
        if not ext:
            return {"provider": self.name, "status": "photo_extension_not_supported", "ok": False, "message": "Extensão de foto não suportada para upload."}
        upload_endpoint = self.config.get("upload_endpoint", "")
        if not upload_endpoint:
            logger.warning("poc_photo_upload_missing_config provider=%s", self.name)
            return {
                "provider": self.name,
                "status": "photo_upload_not_configured",
                "ok": False,
                "message": "Foto recebida pela Bridge, mas upload_endpoint do provider não configurado; imagem não enviada ao iConvNet.",
            }
        image_bytes = file_path.read_bytes()
        upload_headers = {"ext": ext, "Use-Type": "tmp"}
        response = await self._client.post(upload_endpoint, headers=upload_headers, content=image_bytes)
        response.raise_for_status()
        data = response.json()
        remote_file_path = data.get("Ori_file")
        logger.info("poc_photo_upload_response has_ori_file=%s status_code=%s", bool(remote_file_path), response.status_code)
        if not remote_file_path:
            return {"provider": self.name, "status": "photo_upload_missing_ori_file", "ok": False, "message": "Upload da foto concluído sem Ori_file na resposta do provider.", "raw": data}
        event["_remote_file_path"] = remote_file_path
        logger.info("poc_photo_uploaded remote_file_path=%s", remote_file_path)
        return None

    def _map_upload_ext(self, suffix: str) -> str | None:
        normalized = suffix.lower().replace(".", "")
        if normalized == "jpeg":
            return "jpg"
        if normalized in {"jpg", "png", "gif"}:
            return normalized
        return None

    async def close(self) -> None:
        if self._closed or self._client.is_closed:
            return
        self._closed = True
        await self._client.aclose()
