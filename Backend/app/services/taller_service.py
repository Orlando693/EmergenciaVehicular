from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.taller import Taller
from app.models.usuario import Usuario, Rol, UsuarioRol
from app.models.enums import EstadoTallerEnum
from app.schemas.taller import TallerCreate, TallerUpdate, TallerOut, TallerEstadoUpdate
from app.core.security import hash_password


async def registrar_taller(
    id_usuario: int,
    data: TallerCreate,
    db: AsyncSession,
) -> TallerOut:
    existe = await db.execute(select(Taller).where(Taller.id_usuario == id_usuario))
    if existe.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Este usuario ya tiene un taller registrado")

    if data.nit:
        dup = await db.execute(select(Taller).where(Taller.nit == data.nit))
        if dup.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="El NIT ya está registrado")

    taller = Taller(id_usuario=id_usuario, **data.model_dump())
    db.add(taller)
    await db.commit()
    await db.refresh(taller)
    return taller


async def listar_talleres(
    db: AsyncSession,
    estado: EstadoTallerEnum | None = None,
) -> list[TallerOut]:
    query = select(Taller)
    if estado:
        query = query.where(Taller.estado_registro == estado)
    result = await db.execute(query)
    return result.scalars().all()


async def obtener_taller(id_taller: int, db: AsyncSession) -> TallerOut:
    result = await db.execute(select(Taller).where(Taller.id_taller == id_taller))
    taller = result.scalar_one_or_none()
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado")
    return taller


async def obtener_taller_por_usuario(id_usuario: int, db: AsyncSession) -> TallerOut:
    result = await db.execute(select(Taller).where(Taller.id_usuario == id_usuario))
    taller = result.scalar_one_or_none()
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado para este usuario")
    return taller


async def actualizar_taller(id_taller: int, data: TallerUpdate, db: AsyncSession) -> TallerOut:
    result = await db.execute(select(Taller).where(Taller.id_taller == id_taller))
    taller = result.scalar_one_or_none()
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(taller, field, value)

    await db.commit()
    await db.refresh(taller)
    return taller


async def cambiar_estado_taller(
    id_taller: int,
    data: TallerEstadoUpdate,
    db: AsyncSession,
) -> TallerOut:
    result = await db.execute(select(Taller).where(Taller.id_taller == id_taller))
    taller = result.scalar_one_or_none()
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado")

    taller.estado_registro = data.estado_registro
    await db.commit()
    await db.refresh(taller)
    return taller
