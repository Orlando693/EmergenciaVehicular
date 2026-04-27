from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update

from app.models.dispositivo_push import DispositivoPush
from app.models.notificacion import Notificacion
from app.core.ws_manager import ws_manager
from app.services.asignacion_atencion.firebase_push_service import enviar_push_token
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

    await _enviar_push_fcm(db, notif)

    return notif


async def registrar_fcm_token(
    db: AsyncSession,
    id_usuario: int,
    token: str,
    platform: str | None = None,
) -> DispositivoPush:
    result = await db.execute(
        select(DispositivoPush).where(DispositivoPush.fcm_token == token)
    )
    dispositivo = result.scalar_one_or_none()

    if dispositivo:
        dispositivo.id_usuario = id_usuario
        dispositivo.platform = platform
        dispositivo.activo = True
    else:
        dispositivo = DispositivoPush(
            id_usuario=id_usuario,
            fcm_token=token,
            platform=platform,
            activo=True,
        )
        db.add(dispositivo)

    await db.commit()
    await db.refresh(dispositivo)
    return dispositivo


async def _enviar_push_fcm(db: AsyncSession, notif: Notificacion) -> None:
    result = await db.execute(
        select(DispositivoPush).where(
            DispositivoPush.id_usuario == notif.id_usuario,
            DispositivoPush.activo == True,  # noqa: E712
        )
    )
    dispositivos = result.scalars().all()

    if not dispositivos:
        return

    data = {
        "id_notificacion": str(notif.id_notificacion),
        "tipo": notif.tipo,
    }
    if notif.id_incidente:
        data["id_incidente"] = str(notif.id_incidente)

    for dispositivo in dispositivos:
        ok = await enviar_push_token(
            dispositivo.fcm_token,
            notif.titulo,
            notif.mensaje,
            data=data,
        )
        if not ok:
            dispositivo.activo = False

    await db.commit()


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
