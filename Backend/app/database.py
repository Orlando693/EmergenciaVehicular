import logging
import sys
import ssl

if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

_log = logging.getLogger("emergencia.db")

# Aiven: SSL obligatorio. Si en Railway se olvida DB_SSL_REQUIRED, pero la URL
# apunta a aivencloud.com, activar SSL de todos modos.
def _aiven_url() -> bool:
    u = (settings.DATABASE_URL or "").lower()
    return "aivencloud.com" in u

_ssl_on = bool(settings.DB_SSL_REQUIRED) or _aiven_url()

# Aiven (y otros proveedores cloud) requieren SSL. Si el DATABASE_URL
# contiene "aivencloud.com" o la variable DB_SSL_REQUIRED está activa,
# se pasa el contexto SSL a asyncpg.
_ssl_ctx: ssl.SSLContext | None = None
if _ssl_on:
    _ssl_ctx = ssl.create_default_context()
    _ssl_ctx.check_hostname = False
    _ssl_ctx.verify_mode = ssl.CERT_NONE

# Log sin contraseña: ayuda a ver si en Railway el host de Aiven está bien copiado
try:
    _pu = make_url(settings.DATABASE_URL)
    _log.info(
        "Base de datos: host=%r puerto=%r nombre=%r ssl_asyncpg=%s",
        _pu.host,
        _pu.port,
        _pu.database,
        _ssl_on,
    )
except Exception as exc:
    _log.warning("DATABASE_URL no es un URL válida: %s", exc)

_connect_args = {"ssl": _ssl_ctx} if _ssl_ctx else {}

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    connect_args=_connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
