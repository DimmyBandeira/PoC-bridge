import json
import logging
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)


class JsonStorageService:
    def __init__(self, data_dir: str) -> None:
        self._data_dir = Path(data_dir)
        self._data_dir.mkdir(parents=True, exist_ok=True)

    def read_json(self, file_name: str, default: Any) -> Any:
        path = self._data_dir / file_name
        if not path.exists():
            logger.warning("Arquivo JSON não encontrado: %s. Usando valor padrão.", path)
            return default

        try:
            with path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except (OSError, json.JSONDecodeError):
            logger.exception("Falha ao ler JSON: %s", path)
            return default

    def write_json(self, file_name: str, content: Any) -> None:
        path = self._data_dir / file_name
        try:
            with path.open("w", encoding="utf-8") as file:
                json.dump(content, file, indent=2, ensure_ascii=False)
        except OSError:
            logger.exception("Falha ao gravar JSON: %s", path)
            raise
