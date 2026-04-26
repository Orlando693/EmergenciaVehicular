from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.estado_util import texto_estado_usuario
from app.core.security import decode_token
from app.database import get_db
from app.models.usuario import Usuario

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

DBDep = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DBDep,
) -> Usuario:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token_data = decode_token(token)
    except JWTError:
        raise credentials_exception

    result = await db.execute(
        select(Usuario)
        .where(Usuario.id_usuario == token_data.id_usuario)
        .options(selectinload(Usuario.roles))
    )
    usuario = result.scalar_one_or_none()
    if usuario is None or texto_estado_usuario(usuario.estado) != "ACTIVO":
        raise credentials_exception
    return usuario


CurrentUser = Annotated[Usuario, Depends(get_current_user)]


def require_roles(*roles: str):
    """Dependencia de autorización por rol."""
    async def _checker(current_user: CurrentUser) -> Usuario:
        user_roles = {r.nombre for r in current_user.roles}
        if not user_roles.intersection(roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Se requiere uno de los roles: {', '.join(roles)}",
            )
        return current_user
    return _checker
