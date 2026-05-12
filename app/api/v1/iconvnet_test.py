import logging
import os
import re
from typing import Any

from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.core.config import load_config
from app.providers.iconvnet_ai_event_provider import IconvnetAiEventProvider
from app.providers.iconvnet_task_ticket_provider import IconvnetTaskTicketProvider
from app.services.json_storage import JsonStorageService
from app.services.poc_service import poc_service
from app.services.storage import save_uploaded_photo


logger = logging.getLogger(__name__)
router = APIRouter()


class AiEventPhotoUrlRequest(BaseModel):
    image_url: str = Field(min_length=1)
    alarm_name: str | None = None
    dev_name: str | None = None


class TaskTicketRequest(BaseModel):
    title: str = Field(min_length=1)
    notes: str = Field(min_length=1)
    uid: str | int | None = None
    image_urls: list[str] | None = None
    video_urls: list[str] | None = None


def _require_auth(api_key: str | None) -> None:
    auth = poc_service.authenticate_api_key(api_key)
    if auth is None:
        raise HTTPException(status_code=401, detail="API key inválida")


def _resolve_env_config(config: dict[str, Any]) -> dict[str, Any]:
    resolved: dict[str, Any] = {}
    env_pattern = re.compile(r"^\$\{([A-Z0-9_]+)\}$")
    for key, value in config.items():
        if isinstance(value, str):
            match = env_pattern.match(value)
            if match:
                resolved[key] = os.getenv(match.group(1), "")
                continue
        resolved[key] = value
    return resolved


def _load_test_provider_configs() -> tuple[dict[str, Any], dict[str, Any], float]:
    app_config = load_config()
    storage = JsonStorageService(app_config.data_dir)
    provider_configs = storage.read_json("provider_configs.json", default={})
    ai_event_config = _resolve_env_config(provider_configs.get("iconvnet_ai_event", {}))
    task_ticket_config = _resolve_env_config(provider_configs.get("iconvnet_task_ticket", {}))
    return ai_event_config, task_ticket_config, app_config.poc_timeout_seconds


@router.post("/ai-event/photo-base64")
async def ai_event_photo_base64(
    file: UploadFile = File(...),
    alarm_name: str | None = Form(default=None),
    dev_name: str | None = Form(default=None),
    x_api_key: str | None = Header(default=None),
):
    _require_auth(x_api_key)
    photo_path = await save_uploaded_photo(file)
    ai_event_config, _, timeout_seconds = _load_test_provider_configs()
    provider = IconvnetAiEventProvider("iconvnet_ai_event", ai_event_config, timeout_seconds=timeout_seconds)
    try:
        result = await provider.dispatch_photo_base64(photo_path=photo_path, alarm_name=alarm_name, dev_name=dev_name)
        return {"status": "success", **result}
    finally:
        await provider.close()


@router.post("/ai-event/photo-url")
async def ai_event_photo_url(request: AiEventPhotoUrlRequest, x_api_key: str | None = Header(default=None)):
    _require_auth(x_api_key)
    ai_event_config, _, timeout_seconds = _load_test_provider_configs()
    provider = IconvnetAiEventProvider("iconvnet_ai_event", ai_event_config, timeout_seconds=timeout_seconds)
    try:
        result = await provider.dispatch_photo_url(
            image_url=request.image_url,
            alarm_name=request.alarm_name,
            dev_name=request.dev_name,
        )
        return {"status": "success", **result}
    finally:
        await provider.close()


@router.post("/task-ticket")
async def task_ticket(request: TaskTicketRequest, x_api_key: str | None = Header(default=None)):
    _require_auth(x_api_key)
    _, task_ticket_config, timeout_seconds = _load_test_provider_configs()
    provider = IconvnetTaskTicketProvider("iconvnet_task_ticket", task_ticket_config, timeout_seconds=timeout_seconds)
    try:
        result = await provider.create_ticket(
            title=request.title,
            notes=request.notes,
            uid=request.uid,
            image_urls=request.image_urls,
            video_urls=request.video_urls,
        )
        return {"status": "success", **result}
    finally:
        await provider.close()
