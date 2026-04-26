from contextlib import asynccontextmanager
import asyncio
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.config import settings
from app.database import engine, Base, AsyncSessionLocal
from app.models import *  # noqa: F401,F403 – registra todos los modelos en Base.metadata

from app.routers import auth, usuarios, roles, talleres, tecnicos, vehiculos, incidentes, bitacora, notificaciones, chat, pagos, reportes


logger = logging.getLogger("emergencia.api")


async def _init_db_schema() -> None:
    """Crea tablas y tipos ENUM si no existen. Ejecuta en background para no
    bloquear el arranque: Railway hace healthcheck a / pocos segundos después
    de levantar el proceso, y conectar a Aiven + create_all puede superar
    el timeout o fallar con credenciales erróneas."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as exc:
        logger.exception("init db schema failed (revisa DATABASE_URL, SSL, red): %s", exc)
        return


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Importante: no await create_all aquí. Si bloquea, Uvicorn no acepta
    # conexiones y el healthcheck de Railway falla.
    asyncio.create_task(_init_db_schema())
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API REST para la Plataforma Inteligente de Atención de Emergencias Vehiculares",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# - Si CORS_ORIGINS está definido, se usan esos orígenes con credenciales.
# - Si no está definido, se permite "*" SIN credenciales (combinación válida en
#   navegadores; "*" + credenciales no es soportado por la spec de CORS).
if settings.CORS_ORIGINS:
    origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
    allow_credentials = True
else:
    origins = ["*"]
    allow_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
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
# El directorio físico es configurable (settings.UPLOAD_DIR) para que en Railway
# pueda apuntarse a un Volume persistente (ej. /data/uploads). El prefijo URL
# público se mantiene en /public/uploads/* para no romper al frontend ni a los
# registros existentes en BD.
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
        logger.warning(f"Health check DB failed: {exc}")

    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "ok" if db_ok else "degraded",
        "database": "ok" if db_ok else f"error: {db_error}",
    }
