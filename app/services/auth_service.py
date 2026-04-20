from typing import Any


class AuthService:
    def __init__(self, api_keys: list[dict[str, Any]]) -> None:
        self._api_key_map = {entry.get("api_key"): entry for entry in api_keys if entry.get("api_key")}

    def authenticate(self, api_key: str | None) -> dict[str, Any] | None:
        if not api_key:
            return None
        return self._api_key_map.get(api_key)
