from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import verify_password, create_access_token
from app.models.usuario import Usuario
from app.schemas.auth import Token


async def login(email: str, password: str, db: AsyncSession) -> Token:
    result = await db.execute(
        select(Usuario)
        .where(Usuario.email == email)
        .options(selectinload(Usuario.roles))
    )
    usuario = result.scalar_one_or_none()

    if not usuario or not verify_password(password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )
    if usuario.estado.value != "ACTIVO":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"La cuenta está {usuario.estado.value}",
        )

    roles = [r.nombre for r in usuario.roles]

    await db.execute(
        update(Usuario)
        .where(Usuario.id_usuario == usuario.id_usuario)
        .values(ultimo_acceso=datetime.utcnow())
    )
    await db.commit()

    token = create_access_token({
        "sub": str(usuario.id_usuario),
        "email": usuario.email,
        "roles": roles,
    })

    return Token(
        access_token=token,
        token_type="bearer",
        rol=roles[0] if roles else "SIN_ROL",
        id_usuario=usuario.id_usuario,
        nombre=f"{usuario.nombres} {usuario.apellidos}",
    )
