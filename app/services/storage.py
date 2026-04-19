import os
import uuid
import aiofiles
from fastapi import UploadFile
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

STORAGE_PATH = os.getenv("STORAGE_PATH", "./storage")

def ensure_storage_dir():
    """Cria o diretório de storage se não existir."""
    os.makedirs(STORAGE_PATH, exist_ok=True)

async def save_uploaded_photo(file: UploadFile) -> str:
    """
    Salva uma foto enviada na pasta storage/ com nome único.
    Retorna o caminho completo do arquivo salvo.
    """
    ensure_storage_dir()
    
    # Gera nome único: timestamp_uuid.ext
    ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    unique_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}{ext}"
    file_path = os.path.join(STORAGE_PATH, unique_name)
    
    # Salva o arquivo de forma assíncrona
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)
    
    # Retorna o caminho absoluto para ser usado na API PoC
    # Nota: A API PoC espera um caminho acessível no servidor DELES.
    # Como não temos upload para o servidor PoC, retornamos o caminho local.
    # Pode ser necessário configurar um servidor web para servir as imagens.
    # Por enquanto, retornamos o caminho local absoluto.
    abs_path = os.path.abspath(file_path)
    return abs_path