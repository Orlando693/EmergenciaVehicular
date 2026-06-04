import logging

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.estado_util import texto_estado_usuario
from app.core.security import create_access_token, verify_password
from app.administracion.tenants.model import Tenant
from app.administracion.usuarios.model import Usuario
from app.general.auth.schemas import Token

logger = logging.getLogger(__name__)


async def login(email: str, password: str, db: AsyncSession, tenant_slug: str | None = None) -> Token:
    email_norm = (email or "").strip().lower()

    stmt = (
        select(Usuario)
        .where(func.lower(Usuario.email) == email_norm)
        .options(selectinload(Usuario.roles))
    )
    if tenant_slug:
        tenant_res = await db.execute(
            select(Tenant).where(func.lower(Tenant.slug) == tenant_slug.strip().lower())
        )
        t = tenant_res.scalar_one_or_none()
        if not t:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas",
            )
        stmt = stmt.where(Usuario.id_tenant == t.id_tenant)

    result = await db.execute(stmt)
    usuarios = result.scalars().all()

    if len(usuarios) > 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email existe en varios tenants. Indica 'tenant_slug' en el login.",
        )

    usuario = usuarios[0] if usuarios else None

    if not usuario or not verify_password(password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )
    estado_txt = texto_estado_usuario(usuario.estado)
    if estado_txt != "ACTIVO":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"La cuenta está {estado_txt}",
        )

    if usuario.id_tenant is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta no tiene tenant asignado. Ejecuta la migracion multi-tenant.",
        )

    tenant_result = await db.execute(select(Tenant).where(Tenant.id_tenant == usuario.id_tenant))
    tenant = tenant_result.scalar_one_or_none()
    if not tenant or tenant.estado != "ACTIVO":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El tenant de la cuenta no existe o no esta activo",
        )

    roles = [r.nombre for r in usuario.roles]

    # Hora en el servidor PostgreSQL (Aiven): evita 500 por fechas aware/naive con asyncpg
    try:
        await db.execute(
            update(Usuario)
            .where(Usuario.id_usuario == usuario.id_usuario)
            .values(ultimo_acceso=func.now())
        )
        await db.commit()
    except SQLAlchemyError as exc:
        await db.rollback()
        logger.exception("Login: error BD al actualizar ultimo_acceso: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Error de base de datos. Revisa DATABASE_URL y DB_SSL_REQUIRED en Railway.",
        ) from exc

    try:
        token = create_access_token(
            {
                "sub": str(usuario.id_usuario),
                "email": usuario.email,
                "roles": roles,
                "id_tenant": int(usuario.id_tenant),
            }
        )
    except Exception as exc:
        logger.exception("Login: error al generar JWT: %s", exc)
        detail = str(exc) if settings.DEBUG else "Error al generar la sesión"
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail) from exc

    try:
        return Token(
            access_token=token,
            token_type="bearer",
            rol=roles[0] if roles else "SIN_ROL",
            id_usuario=int(usuario.id_usuario),
            nombre=(f"{usuario.nombres or ''} {usuario.apellidos or ''}").strip() or "Usuario",
            id_tenant=int(usuario.id_tenant),
            tenant_nombre=tenant.nombre,
            tenant_slug=tenant.slug,
        )
    except Exception as exc:
        logger.exception("Login: error al validar respuesta: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc) if settings.DEBUG else "Error al completar el login",
        ) from exc
