import logging
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.services.poc_service import poc_service
from app.services.storage import save_uploaded_photo


logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


class TextAlertRequest(BaseModel):
    content: str = Field(min_length=1)
    member: Optional[str] = "all"
    brd_hz: Optional[int] = Field(default=2, ge=1, le=10)


class CancelAlertRequest(BaseModel):
    cache_key: Optional[str] = None
    broad_id: Optional[str] = None


@router.post("/text")
@limiter.limit("5/minute")
async def send_text_alert(request: Request, alert: TextAlertRequest):
    try:
        broad_id = await poc_service.send_text_alert(
            content=alert.content,
            member=alert.member,
            brd_hz=alert.brd_hz,
        )
        cache_key = f"text_alert_{alert.content}_{alert.member}"
        return {
            "status": "success",
            "broad_id": broad_id,
            "cache_key": cache_key,
            "message": "Alerta de texto enviado com sucesso",
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Erro ao enviar alerta de texto")
        raise HTTPException(status_code=500, detail="Falha ao enviar alerta de texto") from exc


@router.post("/photo")
@limiter.limit("5/minute")
async def send_photo_alert(
    request: Request,
    file: UploadFile = File(...),
    text: str = Form(...),
    member: str = Form("all"),
):
    if text is None or not text.strip():
        raise HTTPException(status_code=400, detail="Texto do alerta é obrigatório")

    try:
        photo_path = await save_uploaded_photo(file)
        logger.info("Foto salva em: %s", photo_path)

        broad_id = await poc_service.send_photo_alert(
            photo_path=photo_path,
            text=text,
            member=member,
        )
        cache_key = f"photo_alert_{text}_{member}"
        return {
            "status": "success",
            "broad_id": broad_id,
            "cache_key": cache_key,
            "photo_path": photo_path,
            "message": "Alerta com foto enviado com sucesso",
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Erro ao enviar alerta com foto")
        raise HTTPException(status_code=500, detail="Falha ao enviar alerta com foto") from exc


@router.post("/cancel")
@limiter.limit("5/minute")
async def cancel_alert(request: Request, cancel_req: CancelAlertRequest):
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
        raise HTTPException(status_code=404, detail="Broadcast não encontrado ou já cancelado")
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Erro ao cancelar alerta")
        raise HTTPException(status_code=500, detail="Falha ao cancelar alerta") from exc


@router.on_event("shutdown")
async def shutdown_event():
    await poc_service.close()
