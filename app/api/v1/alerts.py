from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel
from typing import Optional
import logging

from app.services.poc_service import poc_service
from app.services.storage import save_uploaded_photo

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

class TextAlertRequest(BaseModel):
    content: str
    member: Optional[str] = "all"
    brd_hz: Optional[int] = 2

class CancelAlertRequest(BaseModel):
    cache_key: Optional[str] = None
    broad_id: Optional[str] = None

@router.post("/text")
@limiter.limit("5/minute")
async def send_text_alert(request: Request, alert: TextAlertRequest):
    """
    Endpoint para disparar alerta de texto com repetição (Cenário 1).
    O WebGuardião envia o conteúdo do alerta.
    Retorna o broad_id para possível cancelamento futuro.
    """
    try:
        broad_id = await poc_service.send_text_alert(
            content=alert.content,
            member=alert.member,
            brd_hz=alert.brd_hz
        )
        # Também podemos retornar uma cache_key para o WebGuardião usar no cancelamento
        cache_key = f"text_{alert.content}_{alert.member}"
        return {
            "status": "success",
            "broad_id": broad_id,
            "cache_key": cache_key,
            "message": "Alerta de texto enviado com sucesso"
        }
    except Exception as e:
        logger.exception("Erro ao enviar alerta de texto")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/photo")
@limiter.limit("5/minute")
async def send_photo_alert(
    request: Request,
    file: UploadFile = File(...),
    text: str = Form(...),
    member: str = Form("all")
):
    """
    Endpoint para disparar alerta com foto (Cenário 2).
    Recebe o arquivo de imagem e o texto do alerta.
    A foto é salva localmente e o caminho é enviado no campo content.
    """
    try:
        # Salva a foto
        photo_path = await save_uploaded_photo(file)
        logger.info(f"Foto salva em: {photo_path}")
        
        # Envia alerta com foto
        broad_id = await poc_service.send_photo_alert(
            photo_path=photo_path,
            text=text,
            member=member
        )
        cache_key = f"photo_{photo_path}_{text}_{member}"
        return {
            "status": "success",
            "broad_id": broad_id,
            "cache_key": cache_key,
            "photo_path": photo_path,
            "message": "Alerta com foto enviado com sucesso"
        }
    except Exception as e:
        logger.exception("Erro ao enviar alerta com foto")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cancel")
@limiter.limit("5/minute")
async def cancel_alert(request: Request, cancel_req: CancelAlertRequest):
    """
    Endpoint para cancelar um broadcast ativo.
    Pode-se fornecer o broad_id diretamente ou a cache_key retornada na criação.
    """
    try:
        success = False
        if cancel_req.broad_id:
            success = await poc_service.cancel_broadcast(cancel_req.broad_id)
        elif cancel_req.cache_key:
            success = await poc_service.cancel_alert_by_key(cancel_req.cache_key)
        else:
            raise HTTPException(status_code=400, detail="Forneça broad_id ou cache_key")
        
        if success:
            return {"status": "success", "message": "Alerta cancelado"}
        else:
            raise HTTPException(status_code=404, detail="Broadcast não encontrado ou já cancelado")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Erro ao cancelar alerta")
        raise HTTPException(status_code=500, detail=str(e))

@router.on_event("shutdown")
async def shutdown_event():
    await poc_service.close()
