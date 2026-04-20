import os
import uuid
import logging
from datetime import datetime

import aiofiles
from fastapi import HTTPException, UploadFile

from app.core.config import load_config


logger = logging.getLogger(__name__)
_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
_MAX_UPLOAD_BYTES = 5 * 1024 * 1024


def ensure_storage_dir() -> str:
    """Cria o diretório de storage se não existir."""
    storage_path = load_config().storage_path
    os.makedirs(storage_path, exist_ok=True)
    return storage_path


async def save_uploaded_photo(file: UploadFile) -> str:
    """Salva uma foto enviada na pasta storage com nome único e validações básicas."""
    if file is None or not file.filename:
        raise HTTPException(status_code=400, detail="Arquivo inválido")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Extensão não suportada")

    storage_path = ensure_storage_dir()
    unique_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}{ext}"
    file_path = os.path.join(storage_path, unique_name)

    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Arquivo vazio")
        if len(content) > _MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="Arquivo excede tamanho máximo de 5MB")

        async with aiofiles.open(file_path, "wb") as out_file:
            await out_file.write(content)
    except HTTPException:
        raise
    except OSError as exc:
        logger.exception("Erro de IO ao salvar upload")
        raise HTTPException(status_code=500, detail="Falha de IO ao salvar arquivo") from exc

    return os.path.abspath(file_path)
