from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tecnico import Tecnico
from app.models.taller import Taller
from app.schemas.tecnico import TecnicoCreate, TecnicoUpdate, TecnicoOut


async def _verificar_taller(id_taller: int, db: AsyncSession) -> Taller:
    result = await db.execute(select(Taller).where(Taller.id_taller == id_taller))
    taller = result.scalar_one_or_none()
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado")
    return taller


async def crear_tecnico(id_taller: int, data: TecnicoCreate, db: AsyncSession) -> TecnicoOut:
    await _verificar_taller(id_taller, db)
    tecnico = Tecnico(id_taller=id_taller, **data.model_dump())
    db.add(tecnico)
    await db.commit()
    await db.refresh(tecnico)
    return tecnico


async def listar_tecnicos(id_taller: int, db: AsyncSession) -> list[TecnicoOut]:
    await _verificar_taller(id_taller, db)
    result = await db.execute(
        select(Tecnico).where(Tecnico.id_taller == id_taller, Tecnico.activo == True)
    )
    return result.scalars().all()


async def obtener_tecnico(id_tecnico: int, db: AsyncSession) -> TecnicoOut:
    result = await db.execute(select(Tecnico).where(Tecnico.id_tecnico == id_tecnico))
    tecnico = result.scalar_one_or_none()
    if not tecnico:
        raise HTTPException(status_code=404, detail="Técnico no encontrado")
    return tecnico


async def actualizar_tecnico(id_tecnico: int, data: TecnicoUpdate, db: AsyncSession) -> TecnicoOut:
    result = await db.execute(select(Tecnico).where(Tecnico.id_tecnico == id_tecnico))
    tecnico = result.scalar_one_or_none()
    if not tecnico:
        raise HTTPException(status_code=404, detail="Técnico no encontrado")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(tecnico, field, value)

    await db.commit()
    await db.refresh(tecnico)
    return tecnico


async def eliminar_tecnico(id_tecnico: int, db: AsyncSession) -> dict:
    result = await db.execute(select(Tecnico).where(Tecnico.id_tecnico == id_tecnico))
    tecnico = result.scalar_one_or_none()
    if not tecnico:
        raise HTTPException(status_code=404, detail="Técnico no encontrado")
    tecnico.activo = False
    await db.commit()
    return {"detail": "Técnico desactivado correctamente"}
