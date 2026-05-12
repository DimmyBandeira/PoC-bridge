from typing import Any

from app.core.security import generate_sign, get_current_timestamp


def build_iconvnet_auth_headers(config: dict[str, Any]) -> dict[str, str]:
    timestamp = get_current_timestamp()
    app_key = str(config.get("appKey", ""))
    app_secret = str(config.get("appSecret", ""))
    sign = generate_sign(app_key=app_key, app_secret=app_secret, timestamp=timestamp)
    return {"appKey": app_key, "time": str(timestamp), "sign": sign}
