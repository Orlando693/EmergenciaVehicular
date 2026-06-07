from contextlib import asynccontextmanager
import asyncio
import logging
import os
import re

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings
from app.database import engine, Base, AsyncSessionLocal
from app.models import *  # noqa: F401,F403 – registra todos los modelos en Base.metadata

from app.general.auth.router import router as auth_router
from app.administracion.usuarios.router import router as usuarios_router
from app.administracion.roles.router import router as roles_router
from app.administracion.tenants.router import router as tenants_router
from app.operaciones.talleres.router import router as talleres_router
from app.operaciones.tecnicos.router import router as tecnicos_router, taller_tecnicos_router
from app.gestion_vehiculos.vehiculos.router import router as vehiculos_router
from app.gestion_incidentes.incidentes.router import router as incidentes_router
from app.asignacion_atencion.notificaciones.router import router as notificaciones_router
from app.asignacion_atencion.chat.router import router as chat_router
from app.gestion_servicios.pagos.router import router as pagos_router
from app.bitacora_reportes.bitacora.router import router as bitacora_router
from app.bitacora_reportes.reportes.router import router as reportes_router
from app.bitacora_reportes.backup.router import router as backup_router
from app.gestion_operativa_atencion.atencion_tiempo_real.router import router as atencion_tiempo_real_router
from app.gestion_operativa_atencion.sincronizacion_offline.router import router as sincronizacion_offline_router
from app.gestion_operativa_atencion.cotizaciones.router import router as cotizaciones_router
from app.gestion_comercial_servicio.seleccionar_taller_servicio.router import router as seleccionar_taller_router
from app.gestion_operativa_atencion.gestionar_atencion_reparacion.router import router as gestionar_atencion_router
from app.gestion_comercial_servicio.procesar_pago_pasarela.router import router as procesar_pago_router
from app.gestion_comercial_servicio.planes.router import router as planes_router
from app.plataform_superAdmin.router import router as platform_router
from app.gestion_control_analitica_saas.dashboard_operacional.router import router as dashboard_operacional_router
from app.gestion_control_analitica_saas.kpis_atencion.router import router as kpis_atencion_router
from app.gestion_control_analitica_saas.incidentes_analisis.router import router as incidentes_analisis_router
from app.gestion_control_analitica_saas.multi_tenant_admin.router import router as multi_tenant_admin_router


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


def _cors_dict_for_request(request: Request) -> dict[str, str]:
    o = request.headers.get("origin")
    if o and _cors_allows_origin(o):
        return {
            "Access-Control-Allow-Origin": o,
            "Access-Control-Allow-Credentials": "true",
        }
    return {}


def _chain_has_errno(exc: BaseException | None, errno: int) -> bool:
    if exc is None:
        return False
    if isinstance(exc, OSError) and exc.errno == errno:
        return True
    return _chain_has_errno(exc.__cause__, errno) or _chain_has_errno(exc.__context__, errno)


def _public_error_detail(exc: Exception) -> str | None:
    """Mensaje seguro (sin traza) para el cliente cuando conocemos el fallo típico."""
    if _chain_has_errno(exc, 2) or "Name or service not known" in str(exc):
        return (
            "No se puede conectar a PostgreSQL: el nombre del servidor en DATABASE_URL no se resuelve (DNS). "
            "En Railway, abre Variables y pega de nuevo el connection string completo de Aiven (página del servicio → User & DB → conexión). "
            "Sin comillas, sin saltos de línea; contraseña con caracteres raros codificada en la URL. "
            "Hasta que /health muestre database ok, el login no funcionará."
        )
    if "connection refused" in str(exc).lower() or "Connection refused" in str(exc):
        return (
            "Conexión rechazada al puerto de PostgreSQL. Revisa el puerto en DATABASE_URL y el firewall (Aiven debe permitir conexión desde Internet / tu IP, no solo localhost)."
        )
    return None


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
    # Bootstrap defensivo para entornos vacios. Las modificaciones de esquema en
    # tablas existentes deben aplicarse con Alembic, no con create_all().
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


# Errores 4xx/5xx no pasan por el middleware (BaseHTTPMiddleware no añade CORS
# a respuestas generadas por excepción). Añadimos CORS en los handlers.
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    h = _cors_dict_for_request(request)
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
        headers=h,
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    h = _cors_dict_for_request(request)
    if exc.headers:
        h.update(dict(exc.headers))
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=h,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Error no manejado en %s %s: %s", request.method, request.url.path, exc)
    h = _cors_dict_for_request(request)
    public = _public_error_detail(exc)
    if public:
        msg = public
    elif settings.DEBUG:
        msg = str(exc)
    else:
        msg = "Error interno"
    return JSONResponse(status_code=500, content={"detail": msg}, headers=h)


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(usuarios_router)
app.include_router(roles_router)
app.include_router(tenants_router)
app.include_router(talleres_router)
app.include_router(tecnicos_router)
app.include_router(taller_tecnicos_router)
app.include_router(vehiculos_router)
app.include_router(incidentes_router)
app.include_router(bitacora_router)
app.include_router(notificaciones_router)
app.include_router(chat_router)
app.include_router(pagos_router)
app.include_router(reportes_router)
app.include_router(backup_router)
app.include_router(atencion_tiempo_real_router)
app.include_router(sincronizacion_offline_router)
app.include_router(cotizaciones_router)
app.include_router(seleccionar_taller_router)
app.include_router(gestionar_atencion_router)
app.include_router(procesar_pago_router)
app.include_router(planes_router)
app.include_router(platform_router)
app.include_router(dashboard_operacional_router)
app.include_router(kpis_atencion_router)
app.include_router(incidentes_analisis_router)
app.include_router(multi_tenant_admin_router)

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
