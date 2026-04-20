import logging
from typing import Any

from app.services.provider_registry import ProviderRegistry


logger = logging.getLogger(__name__)


class DispatchService:
    def __init__(self, provider_registry: ProviderRegistry) -> None:
        self._provider_registry = provider_registry

    async def dispatch(self, event: dict[str, Any], provider_names: list[str]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for provider_name in provider_names:
            provider = self._provider_registry.get(provider_name)
            if provider is None:
                logger.warning("Provider não encontrado no registry: %s", provider_name)
                continue
            result = await provider.dispatch(event)
            results.append(result)
        return results

    async def cancel(self, payload: dict[str, Any], provider_names: list[str]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for provider_name in provider_names:
            provider = self._provider_registry.get(provider_name)
            if provider is None:
                logger.warning("Provider não encontrado no registry para cancel: %s", provider_name)
                continue
            result = await provider.cancel(payload)
            results.append(result)
        return results
