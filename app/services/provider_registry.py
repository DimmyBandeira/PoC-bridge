import logging
from typing import Any

from app.providers.base import BaseProvider
from app.providers.poc_provider import PoCProvider
from app.providers.teams_provider import TeamsProvider
from app.providers.whatsapp_provider import WhatsAppProvider


logger = logging.getLogger(__name__)


class ProviderRegistry:
    def __init__(self, provider_configs: dict[str, Any], timeout_seconds: float = 8.0) -> None:
        self._providers: dict[str, BaseProvider] = {}
        self._timeout_seconds = timeout_seconds
        self._build_providers(provider_configs)

    def _build_providers(self, provider_configs: dict[str, Any]) -> None:
        for provider_name, config in provider_configs.items():
            provider_type = (config.get("type") or "").lower()
            if provider_type == "poc":
                self._providers[provider_name] = PoCProvider(
                    name=provider_name,
                    config=config,
                    timeout_seconds=self._timeout_seconds,
                )
            elif provider_type == "whatsapp":
                self._providers[provider_name] = WhatsAppProvider(name=provider_name, config=config)
            elif provider_type == "teams":
                self._providers[provider_name] = TeamsProvider(name=provider_name, config=config)
            else:
                logger.warning("Provider desconhecido ignorado: %s", provider_name)

    def get(self, provider_name: str) -> BaseProvider | None:
        return self._providers.get(provider_name)

    async def close(self) -> None:
        for provider in self._providers.values():
            close_fn = getattr(provider, "close", None)
            if callable(close_fn):
                await close_fn()
