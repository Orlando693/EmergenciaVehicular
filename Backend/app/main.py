from contextlib import asynccontextmanager
import asyncio
import logging
import os
import re

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings
from app.database import engine, Base, AsyncSessionLocal
from app.models import *  # noqa: F401,F403 – registra todos los modelos en Base.metadata

from app.routers import auth, usuarios, roles, talleres, tecnicos, vehiculos, incidentes, bitacora, notificaciones, chat, pagos, reportes


logger = logging.getLogger("emergencia.api")

# Orígenes que NUNCA deben faltar (CORS_ORIGINS en Railway puede pisar y dejar solo localhost).
_CORS_MANDATORY = (
    "https://parcial1si2.web.app,https://parcial1si2.firebaseapp.com,"
    "http://localhost:4200,http://127.0.0.1:4200,http://localhost:3000,http://127.0.0.1:3000"
)
_CORS_ORIGIN_REGEX = r"^https://parcial1si2\.(web\.app|firebaseapp\.com)$"


def _merge_cors_origins() -> list[str]:
    out: set[str] = set()
    for raw in (_CORS_MANDATORY + "," + (settings.CORS_ORIGINS or "")).split(","):
        o = raw.strip().rstrip("/")
        if o:
            out.add(o)
    return sorted(out)


_CORS_ALLOW_SET: frozenset[str] = frozenset(_merge_cors_origins())
_CORS_ALLOW_RE = re.compile(_CORS_ORIGIN_REGEX)


def _cors_allows_origin(origin: str | None) -> bool:
    if not origin:
        return False
    if origin in _CORS_ALLOW_SET:
        return True
    return _CORS_ALLOW_RE.fullmatch(origin) is not None


def _apply_cors_response_headers(response: Response, origin: str) -> None:
    response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Vary"] = "Origin"


class CORSEnforceMiddleware(BaseHTTPMiddleware):
    """
    CORS explícito. CORSMiddleware de Starlette a veces no añade cabeceras en
    producción; este middleware asegura preflight (OPTIONS) y cabeceras en la
    respuesta real (GET/POST/...).
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        origin = request.headers.get("origin")

        if request.method == "OPTIONS":
            if not origin or not _cors_allows_origin(origin):
                return Response(status_code=403, content="CORS: origin not allowed", media_type="text/plain")
            acrh = request.headers.get("access-control-request-headers")
            hdrs: dict[str, str] = {
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT",
                "Access-Control-Max-Age": "86400",
                "Access-Control-Allow-Headers": (
                    acrh or "accept, authorization, content-type, x-requested-with"
                ),
            }
            return Response(status_code=200, content="", media_type="text/plain", headers=hdrs)

        response = await call_next(request)
        if origin and _cors_allows_origin(origin):
            _apply_cors_response_headers(response, origin)
        return response


async def _init_db_schema() -> None:
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as exc:
        logger.exception("init db schema failed (revisa DATABASE_URL, SSL, red): %s", exc)
        return


@asynccontextmanager
async def lifespan(_app: FastAPI):
    asyncio.create_task(_init_db_schema())
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API REST para la Plataforma Inteligente de Atención de Emergencias Vehiculares",
    lifespan=lifespan,
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(roles.router)
app.include_router(talleres.router)
app.include_router(tecnicos.router)
app.include_router(vehiculos.router)
app.include_router(incidentes.router)
app.include_router(bitacora.router)
app.include_router(notificaciones.router)
app.include_router(chat.router)
app.include_router(pagos.router)
app.include_router(reportes.router)

# ── Static uploads ────────────────────────────────────────────────────────────
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount(
    settings.UPLOAD_URL_PREFIX,
    StaticFiles(directory=settings.UPLOAD_DIR),
    name="uploads",
)


@app.get("/", tags=["Health"])
async def root():
    return {"app": settings.APP_NAME, "version": settings.APP_VERSION, "status": "ok"}


@app.get("/health", tags=["Health"])
async def health():
    """Healthcheck que también verifica conectividad a la BD."""
    db_ok = False
    db_error: str | None = None
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        db_ok = True
    except Exception as exc:
        db_error = str(exc)
        logger.warning("Health check DB failed: %s", exc)

    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "ok" if db_ok else "degraded",
        "database": "ok" if db_ok else f"error: {db_error}",
    }


# CORS: registrar al final; envuelve rutas, mounts y /health
app.add_middleware(CORSEnforceMiddleware)
logger.info(
    "CORS activo. Orígenes: %d | regex: %s",
    len(_CORS_ALLOW_SET),
    _CORS_ORIGIN_REGEX,
)
