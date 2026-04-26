from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update

from app.models.notificacion import Notificacion
from app.core.ws_manager import ws_manager
import logging

logger = logging.getLogger(__name__)


async def crear_notificacion(
    db: AsyncSession,
    id_usuario: int,
    titulo: str,
    mensaje: str,
    tipo: str = "INFO",
    id_incidente: int | None = None,
) -> Notificacion:
    notif = Notificacion(
        id_usuario=id_usuario,
        id_incidente=id_incidente,
        titulo=titulo,
        mensaje=mensaje,
        tipo=tipo,
    )
    db.add(notif)
    await db.commit()
    await db.refresh(notif)

    # Intentar enviar en tiempo real via WebSocket
    try:
        await ws_manager.push(id_usuario, {
            "id_notificacion": notif.id_notificacion,
            "titulo": notif.titulo,
            "mensaje": notif.mensaje,
            "tipo": notif.tipo,
            "id_incidente": notif.id_incidente,
            "leida": notif.leida,
            "created_at": notif.created_at.isoformat(),
        })
    except Exception as exc:
        logger.warning(f"[Notificacion] WS push fallido para usuario {id_usuario}: {exc}")

    return notif


async def listar_notificaciones(db: AsyncSession, id_usuario: int, skip: int = 0, limit: int = 20):
    total_r = await db.execute(
        select(func.count()).where(Notificacion.id_usuario == id_usuario).select_from(Notificacion)
    )
    total = total_r.scalar_one()

    no_leidas_r = await db.execute(
        select(func.count()).where(
            Notificacion.id_usuario == id_usuario,
            Notificacion.leida == False  # noqa: E712
        ).select_from(Notificacion)
    )
    no_leidas = no_leidas_r.scalar_one()

    items_r = await db.execute(
        select(Notificacion)
        .where(Notificacion.id_usuario == id_usuario)
        .order_by(Notificacion.created_at.desc())
        .offset(skip).limit(limit)
    )
    items = items_r.scalars().all()

    return {"items": items, "total": total, "no_leidas": no_leidas}


async def contar_no_leidas(db: AsyncSession, id_usuario: int) -> int:
    r = await db.execute(
        select(func.count()).where(
            Notificacion.id_usuario == id_usuario,
            Notificacion.leida == False  # noqa: E712
        ).select_from(Notificacion)
    )
    return r.scalar_one()


async def marcar_leida(db: AsyncSession, id_notificacion: int, id_usuario: int) -> bool:
    r = await db.execute(
        select(Notificacion).where(
            Notificacion.id_notificacion == id_notificacion,
            Notificacion.id_usuario == id_usuario,
        )
    )
    notif = r.scalar_one_or_none()
    if not notif:
        return False
    notif.leida = True
    await db.commit()
    return True


async def marcar_todas_leidas(db: AsyncSession, id_usuario: int):
    await db.execute(
        update(Notificacion)
        .where(Notificacion.id_usuario == id_usuario, Notificacion.leida == False)  # noqa: E712
        .values(leida=True)
    )
    await db.commit()
