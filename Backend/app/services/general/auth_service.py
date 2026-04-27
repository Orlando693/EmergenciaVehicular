import logging

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.estado_util import texto_estado_usuario
from app.core.security import create_access_token, verify_password
from app.models.usuario import Usuario
from app.schemas.auth import Token

logger = logging.getLogger(__name__)


async def login(email: str, password: str, db: AsyncSession) -> Token:
    # Normalizar: BD puede tener mezcla de mayúsculas; el admin de crear_admin se guarda en minúsculas
    email_norm = (email or "").strip().lower()
    result = await db.execute(
        select(Usuario)
        .where(func.lower(Usuario.email) == email_norm)
        .options(selectinload(Usuario.roles))
    )
    usuario = result.scalar_one_or_none()

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
        )
    except Exception as exc:
        logger.exception("Login: error al validar respuesta: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc) if settings.DEBUG else "Error al completar el login",
        ) from exc
