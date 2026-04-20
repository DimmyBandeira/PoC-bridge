import logging
from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.services.poc_service import poc_service


logger = logging.getLogger(__name__)
router = APIRouter()


class DispatchEventRequest(BaseModel):
    partner_id: str = Field(min_length=1)
    event_type: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)


class CancelEventRequest(BaseModel):
    dispatch_id: str = Field(min_length=1)


@router.post("/dispatch")
async def dispatch_event(request: DispatchEventRequest, x_api_key: str | None = Header(default=None)):
    auth = poc_service.authenticate_api_key(x_api_key)
    if auth is None:
        raise HTTPException(status_code=401, detail="API key inválida")

    if auth.get("partner_id") != request.partner_id:
        raise HTTPException(status_code=403, detail="API key não autorizada para este parceiro")

    try:
        result = await poc_service.dispatch_event(
            partner_id=request.partner_id,
            event_type=request.event_type,
            payload=request.payload,
        )
        return {"status": "success", **result}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Erro no dispatch genérico")
        raise HTTPException(status_code=500, detail="Falha ao processar dispatch") from exc


@router.post("/cancel")
async def cancel_event(request: CancelEventRequest, x_api_key: str | None = Header(default=None)):
    auth = poc_service.authenticate_api_key(x_api_key)
    if auth is None:
        raise HTTPException(status_code=401, detail="API key inválida")

    try:
        result = await poc_service.cancel_dispatch(dispatch_id=request.dispatch_id)
        if not result.get("canceled"):
            raise HTTPException(status_code=404, detail="Dispatch não encontrado")
        return {"status": "success", **result}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Erro no cancel genérico")
        raise HTTPException(status_code=500, detail="Falha ao cancelar dispatch") from exc
