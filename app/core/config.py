import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    data_dir: str
    storage_path: str
    log_dir: str
    poc_timeout_seconds: float


def load_config() -> AppConfig:
    return AppConfig(
        data_dir=os.getenv("DATA_DIR", "./app/data"),
        storage_path=os.getenv("STORAGE_PATH", "./storage"),
        log_dir=os.getenv("LOG_DIR", "./app/logs"),
        poc_timeout_seconds=float(os.getenv("POC_TIMEOUT_SECONDS", "8.0")),
    )
