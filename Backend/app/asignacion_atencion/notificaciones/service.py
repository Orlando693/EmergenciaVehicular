from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update

from app.asignacion_atencion.notificaciones.model import DispositivoPush, Notificacion
from app.administracion.usuarios.model import Usuario
from app.core.ws_manager import ws_manager
from app.asignacion_atencion.notificaciones.push_service import enviar_push_token
import logging

logger = logging.getLogger(__name__)


async def crear_notificacion(
    db: AsyncSession,
    id_usuario: int,
    titulo: str,
    mensaje: str,
    tipo: str = "INFO",
    id_incidente: int | None = None,
    id_tenant: int | None = None,
) -> Notificacion:
    if id_tenant is None:
        usuario_r = await db.execute(select(Usuario).where(Usuario.id_usuario == id_usuario))
        usuario = usuario_r.scalar_one_or_none()
        if usuario:
            id_tenant = usuario.id_tenant
    if id_tenant is None:
        raise ValueError("No se pudo determinar el tenant de la notificacion")

    notif = Notificacion(
        id_tenant=id_tenant,
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
    id_tenant: int,
    token: str,
    platform: str | None = None,
) -> DispositivoPush:
    result = await db.execute(
        select(DispositivoPush).where(DispositivoPush.fcm_token == token, DispositivoPush.id_tenant == id_tenant)
    )
    dispositivo = result.scalar_one_or_none()

    if dispositivo:
        dispositivo.id_usuario = id_usuario
        dispositivo.id_tenant = id_tenant
        dispositivo.platform = platform
        dispositivo.activo = True
    else:
        dispositivo = DispositivoPush(
            id_usuario=id_usuario,
            id_tenant=id_tenant,
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
            DispositivoPush.id_tenant == notif.id_tenant,
            DispositivoPush.activo == True,  # noqa: E712
        )
    )
    dispositivos = result.scalars().all()

    if not dispositivos:
        logger.warning(
            "[Notificacion] Usuario %s no tiene dispositivos FCM activos para notificacion %s",
            notif.id_usuario,
            notif.id_notificacion,
        )
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
        if ok is True:
            logger.info(
                "[Notificacion] FCM enviado a usuario %s dispositivo %s",
                notif.id_usuario,
                dispositivo.id_dispositivo,
            )
        elif ok is False:
            logger.warning(
                "[Notificacion] FCM rechazo token, desactivando dispositivo %s",
                dispositivo.id_dispositivo,
            )
            dispositivo.activo = False
        else:
            logger.warning(
                "[Notificacion] FCM no enviado por configuracion del servidor; token se mantiene activo para dispositivo %s",
                dispositivo.id_dispositivo,
            )

    await db.commit()


async def listar_notificaciones(db: AsyncSession, id_usuario: int, id_tenant: int, skip: int = 0, limit: int = 20):
    total_r = await db.execute(
        select(func.count()).where(Notificacion.id_usuario == id_usuario, Notificacion.id_tenant == id_tenant).select_from(Notificacion)
    )
    total = total_r.scalar_one()

    no_leidas_r = await db.execute(
        select(func.count()).where(
            Notificacion.id_usuario == id_usuario,
            Notificacion.id_tenant == id_tenant,
            Notificacion.leida == False  # noqa: E712
        ).select_from(Notificacion)
    )
    no_leidas = no_leidas_r.scalar_one()

    items_r = await db.execute(
        select(Notificacion)
        .where(Notificacion.id_usuario == id_usuario, Notificacion.id_tenant == id_tenant)
        .order_by(Notificacion.created_at.desc())
        .offset(skip).limit(limit)
    )
    items = items_r.scalars().all()

    return {"items": items, "total": total, "no_leidas": no_leidas}


async def contar_no_leidas(db: AsyncSession, id_usuario: int, id_tenant: int) -> int:
    r = await db.execute(
        select(func.count()).where(
            Notificacion.id_usuario == id_usuario,
            Notificacion.id_tenant == id_tenant,
            Notificacion.leida == False  # noqa: E712
        ).select_from(Notificacion)
    )
    return r.scalar_one()


async def marcar_leida(db: AsyncSession, id_notificacion: int, id_usuario: int, id_tenant: int) -> bool:
    r = await db.execute(
        select(Notificacion).where(
            Notificacion.id_notificacion == id_notificacion,
            Notificacion.id_usuario == id_usuario,
            Notificacion.id_tenant == id_tenant,
        )
    )
    notif = r.scalar_one_or_none()
    if not notif:
        return False
    notif.leida = True
    await db.commit()
    return True


async def marcar_todas_leidas(db: AsyncSession, id_usuario: int, id_tenant: int):
    await db.execute(
        update(Notificacion)
        .where(Notificacion.id_usuario == id_usuario, Notificacion.id_tenant == id_tenant, Notificacion.leida == False)  # noqa: E712
        .values(leida=True)
    )
    await db.commit()
