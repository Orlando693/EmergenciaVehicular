from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, delete

from app.models.bitacora import Bitacora
from app.schemas.bitacora import BitacoraCreate


async def create_log(db: AsyncSession, log_data: BitacoraCreate) -> Bitacora:
    db_log = Bitacora(
        modulo=log_data.modulo,
        accion=log_data.accion,
        ip=log_data.ip,
        rol=log_data.rol,
        usuario_email=log_data.usuario_email,
        id_usuario=log_data.id_usuario,
    )
    db.add(db_log)
    await db.commit()
    await db.refresh(db_log)
    return db_log


async def get_logs(db: AsyncSession, skip: int = 0, limit: int = 20):
    count_result = await db.execute(select(func.count()).select_from(Bitacora))
    total = count_result.scalar_one()

    result = await db.execute(
        select(Bitacora)
        .order_by(desc(Bitacora.created_at))
        .offset(skip)
        .limit(limit)
    )
    items = result.scalars().all()
    return {"items": items, "total": total}


async def delete_all_logs(db: AsyncSession) -> int:
    count_result = await db.execute(select(func.count()).select_from(Bitacora))
    total = count_result.scalar_one()
    await db.execute(delete(Bitacora))
    await db.commit()
    return total
