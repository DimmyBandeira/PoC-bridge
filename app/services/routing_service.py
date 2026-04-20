from typing import Any


class RoutingService:
    def __init__(self, rules: list[dict[str, Any]]) -> None:
        self._rules = rules

    def resolve_providers(self, partner_id: str, event_type: str) -> list[str]:
        resolved: list[str] = []
        for rule in self._rules:
            if rule.get("partner_id") != partner_id:
                continue
            rule_event_type = rule.get("event_type", "*")
            if rule_event_type not in {"*", event_type}:
                continue
            providers = rule.get("providers", [])
            if isinstance(providers, list):
                resolved.extend([item for item in providers if isinstance(item, str)])
        return list(dict.fromkeys(resolved))
