import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1 import alerts, events
from app.core.config import load_config
from app.core.logging_config import configure_logging
from app.services.poc_service import poc_service
from app.services.storage import ensure_storage_dir

config = load_config()
configure_logging(log_dir=config.log_dir)
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_storage_dir()
    logger.info("PoC Bridge API iniciada. Diretório de storage verificado.")
    yield
    await poc_service.close()
    logger.info("PoC Bridge API encerrada.")


app = FastAPI(
    title="PoC Bridge API",
    description="Middleware entre WebGuardião e iConvNet PoC",
    version="1.1.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["alerts"])
app.include_router(events.router, prefix="/api/v1/events", tags=["events"])


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
