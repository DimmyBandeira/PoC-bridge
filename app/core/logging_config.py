import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


_LOGGING_CONFIGURED = False


def configure_logging(log_dir: str = "./app/logs", log_file: str = "poc_bridge.log") -> None:
    """Configure application logging in an idempotent way."""
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED:
        return

    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    if not root_logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    file_handler = RotatingFileHandler(
        log_path / log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    _LOGGING_CONFIGURED = True
