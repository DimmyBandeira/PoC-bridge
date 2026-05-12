import logging
import asyncio
import uuid
from typing import Any

from app.core.config import load_config
from app.services.auth_service import AuthService
from app.services.dispatch_service import DispatchService
from app.services.json_storage import JsonStorageService
from app.services.provider_registry import ProviderRegistry
from app.services.routing_service import RoutingService


logger = logging.getLogger(__name__)


class PoCService:
    def __init__(self) -> None:
        self._config = load_config()
        self._storage = JsonStorageService(self._config.data_dir)

        self._api_keys = self._storage.read_json("api_keys.json", default=[])
        self._partners = self._storage.read_json("partners.json", default=[])
        self._routing_rules = self._storage.read_json("routing_rules.json", default=[])
        self._provider_configs = self._storage.read_json("provider_configs.json", default={})
        self._state = self._storage.read_json("state.json", default={"dispatches": {}})

        self.auth_service = AuthService(self._api_keys)
        self.routing_service = RoutingService(self._routing_rules)
        self.provider_registry = ProviderRegistry(
            self._provider_configs,
            timeout_seconds=self._config.poc_timeout_seconds,
        )
        self.dispatch_service = DispatchService(self.provider_registry)
        self._closed = False

    def _save_state(self) -> None:
        self._storage.write_json("state.json", self._state)

    def _partner_exists(self, partner_id: str) -> bool:
        return any(partner.get("id") == partner_id for partner in self._partners)

    async def dispatch_event(self, partner_id: str, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self._partner_exists(partner_id):
            raise ValueError(f"Partner não encontrado: {partner_id}")

        providers = self.routing_service.resolve_providers(partner_id=partner_id, event_type=event_type)
        if not providers:
            logger.warning("Nenhum provider roteado para partner=%s event_type=%s", partner_id, event_type)
            return {"dispatch_id": None, "providers": [], "results": []}

        dispatch_id = str(uuid.uuid4())
        event = {"partner": partner_id, "event_type": event_type, **payload}
        results = await self.dispatch_service.dispatch(event=event, provider_names=providers)

        self._state.setdefault("dispatches", {})[dispatch_id] = {
            "partner_id": partner_id,
            "event_type": event_type,
            "providers": providers,
            "payload": payload,
            "results": results,
        }
        self._save_state()

        return {"dispatch_id": dispatch_id, "providers": providers, "results": results}

    async def cancel_dispatch(self, dispatch_id: str) -> dict[str, Any]:
        dispatch_data = self._state.get("dispatches", {}).get(dispatch_id)
        if not dispatch_data:
            return {"dispatch_id": dispatch_id, "canceled": False, "results": []}

        provider_payloads = self._build_cancel_payloads(dispatch_id, dispatch_data)
        results: list[dict[str, Any]] = []
        for provider_name in dispatch_data.get("providers", []):
            payload = provider_payloads.get(provider_name)
            if payload is None:
                logger.warning("Cancel sem broad_id para provider=%s dispatch_id=%s", provider_name, dispatch_id)
                results.append(
                    {
                        "provider": provider_name,
                        "status": "missing_provider_broad_id",
                        "ok": False,
                        "message": "Não foi encontrado broad_id para este provider no histórico do dispatch.",
                    }
                )
                continue
            provider_result = await self.dispatch_service.cancel(payload=payload, provider_names=[provider_name])
            results.extend(provider_result)

        self._state.get("dispatches", {}).pop(dispatch_id, None)
        self._save_state()

        return {"dispatch_id": dispatch_id, "canceled": True, "results": results}

    def _build_cancel_payloads(self, dispatch_id: str, dispatch_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
        payloads: dict[str, dict[str, Any]] = {}
        fallback_broad_id = dispatch_data.get("payload", {}).get("broad_id")
        for result in dispatch_data.get("results", []):
            provider_name = result.get("provider")
            if not provider_name:
                continue
            nested_result = result.get("result", {}) if isinstance(result.get("result"), dict) else {}
            provider_broad_id = (
                result.get("broad_id")
                or result.get("id")
                or nested_result.get("broad_id")
                or nested_result.get("id")
                or fallback_broad_id
            )
            if provider_broad_id:
                payloads[provider_name] = {
                    "dispatch_id": dispatch_id,
                    "provider_broad_id": provider_broad_id,
                    "broad_id": provider_broad_id,
                }
        return payloads

    async def send_text_alert(self, content: str, member: str | None = "all", brd_hz: int | None = 2) -> str:
        payload: dict[str, Any] = {
            "content": content,
            "member": member or "all",
            "brd_hz": brd_hz or 2,
        }
        response = await self.dispatch_event(partner_id="legacy", event_type="text_alert", payload=payload)
        return response.get("dispatch_id") or ""

    async def send_photo_alert(self, photo_path: str, text: str, member: str | None = "all") -> str:
        payload: dict[str, Any] = {
            "photo_path": photo_path,
            "text": text,
            "content": text,
            "member": member or "all",
            "brd_hz": 2,
        }
        response = await self.dispatch_event(partner_id="legacy", event_type="photo_alert", payload=payload)
        return response.get("dispatch_id") or ""

    async def cancel_broadcast(self, broad_id: str) -> bool:
        result = await self.cancel_dispatch(dispatch_id=broad_id)
        return result.get("canceled", False)

    async def cancel_alert_by_key(self, cache_key: str) -> bool:
        dispatches = self._state.get("dispatches", {})
        for dispatch_id, data in dispatches.items():
            payload = data.get("payload", {})
            possible_key = f"{data.get('event_type')}_{payload.get('content', '')}_{payload.get('member', 'all')}"
            if cache_key == possible_key:
                result = await self.cancel_dispatch(dispatch_id=dispatch_id)
                return result.get("canceled", False)
        return False

    def authenticate_api_key(self, api_key: str | None) -> dict[str, Any] | None:
        return self.auth_service.authenticate(api_key)

    async def close(self) -> None:
        if self._closed:
            logger.debug("PoCService.close ignorado: já fechado.")
            return
        self._closed = True
        try:
            await self.provider_registry.close()
        except asyncio.CancelledError:
            logger.info("PoCService.close cancelado durante shutdown.")
            raise
        except Exception:
            logger.exception("Erro ao fechar PoCService.")


poc_service = PoCService()
