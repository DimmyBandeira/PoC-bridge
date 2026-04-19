import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.api.v1 import alerts
from app.services.storage import ensure_storage_dir

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rate limiter global (5 req/min por IP)
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: garantir que o diretório de storage existe
    ensure_storage_dir()
    logger.info("PoC Bridge API iniciada. Diretório de storage verificado.")
    yield
    # Shutdown: limpeza opcional
    logger.info("PoC Bridge API encerrada.")

app = FastAPI(
    title="PoC Bridge API",
    description="Middleware entre WebGuardião e iConvNet PoC",
    version="1.0.0",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configuração CORS (ajuste conforme necessidade)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, restrinja ao IP do WebGuardião
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclui as rotas da API v1
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["alerts"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}