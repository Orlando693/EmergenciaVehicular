from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.operaciones.talleres.model import Taller
from app.operaciones.tecnicos.model import Tecnico
from app.operaciones.tecnicos.schemas import TecnicoCreate, TecnicoOut, TecnicoUpdate


async def _verificar_taller(id_taller: int, id_tenant: int, db: AsyncSession) -> Taller:
    result = await db.execute(select(Taller).where(Taller.id_taller == id_taller, Taller.id_tenant == id_tenant))
    taller = result.scalar_one_or_none()
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado")
    return taller


async def crear_tecnico(id_taller: int, id_tenant: int, data: TecnicoCreate, db: AsyncSession) -> TecnicoOut:
    await _verificar_taller(id_taller, id_tenant, db)
    tecnico = Tecnico(id_taller=id_taller, id_tenant=id_tenant, **data.model_dump())
    db.add(tecnico)
    await db.commit()
    await db.refresh(tecnico)
    return tecnico


async def listar_tecnicos(id_taller: int, id_tenant: int, db: AsyncSession) -> list[TecnicoOut]:
    await _verificar_taller(id_taller, id_tenant, db)
    result = await db.execute(
        select(Tecnico).where(Tecnico.id_taller == id_taller, Tecnico.id_tenant == id_tenant, Tecnico.activo == True)
    )
    return result.scalars().all()


async def listar_todos_tecnicos(id_tenant: int, db: AsyncSession) -> list[TecnicoOut]:
    """Lista todos los técnicos activos del tenant (uso del ADMINISTRADOR)."""
    result = await db.execute(
        select(Tecnico).where(Tecnico.id_tenant == id_tenant, Tecnico.activo == True)
    )
    return result.scalars().all()


async def obtener_tecnico(id_tecnico: int, id_taller: int, id_tenant: int, db: AsyncSession) -> TecnicoOut:
    result = await db.execute(
        select(Tecnico).where(
            Tecnico.id_tecnico == id_tecnico,
            Tecnico.id_taller == id_taller,
            Tecnico.id_tenant == id_tenant,
        )
    )
    tecnico = result.scalar_one_or_none()
    if not tecnico:
        raise HTTPException(status_code=404, detail="Tecnico no encontrado")
    return tecnico


async def actualizar_tecnico(id_tecnico: int, id_taller: int, id_tenant: int, data: TecnicoUpdate, db: AsyncSession) -> TecnicoOut:
    tecnico = await obtener_tecnico(id_tecnico, id_taller, id_tenant, db)

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(tecnico, field, value)

    await db.commit()
    await db.refresh(tecnico)
    return tecnico


async def eliminar_tecnico(id_tecnico: int, id_taller: int, id_tenant: int, db: AsyncSession) -> dict:
    tecnico = await obtener_tecnico(id_tecnico, id_taller, id_tenant, db)
    tecnico.activo = False
    await db.commit()
    return {"detail": "Tecnico desactivado correctamente"}
