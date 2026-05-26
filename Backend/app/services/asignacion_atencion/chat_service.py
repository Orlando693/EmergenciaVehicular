from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status
import logging

from app.models.mensaje_chat import MensajeChat
from app.models.incidente import Incidente
from app.models.cliente import Cliente
from app.models.taller import Taller
from app.models.notificacion import Notificacion
from app.services.asignacion_atencion import notificacion_service

logger = logging.getLogger(__name__)


async def verificar_acceso_chat(
    id_incidente: int,
    id_usuario: int,
    rol: str,
    db: AsyncSession,
) -> Incidente:
    """Verifica que el usuario tiene derecho a acceder al chat de este incidente."""
    r = await db.execute(select(Incidente).where(Incidente.id_incidente == id_incidente))
    incidente = r.scalar_one_or_none()

    if not incidente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incidente no encontrado")

    if incidente.id_taller is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El incidente aún no tiene taller asignado; el chat no está disponible.",
        )

    if rol == "ADMINISTRADOR":
        return incidente

    if rol == "CLIENTE":
        cr = await db.execute(select(Cliente).where(Cliente.id_usuario == id_usuario))
        cliente = cr.scalar_one_or_none()
        if not cliente or cliente.id_cliente != incidente.id_cliente:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes acceso a este chat")

    elif rol == "TALLER":
        tr = await db.execute(select(Taller).where(Taller.id_usuario == id_usuario))
        taller = tr.scalar_one_or_none()
        if not taller or taller.id_taller != incidente.id_taller:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes acceso a este chat")

    return incidente


async def obtener_mensajes(
    id_incidente: int,
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
) -> dict:
    total_r = await db.execute(
        select(func.count())
        .where(MensajeChat.id_incidente == id_incidente)
        .select_from(MensajeChat)
    )
    total = total_r.scalar_one()

    msgs_r = await db.execute(
        select(MensajeChat)
        .where(MensajeChat.id_incidente == id_incidente)
        .order_by(MensajeChat.created_at.asc())
        .offset(skip).limit(limit)
    )
    return {"mensajes": msgs_r.scalars().all(), "total": total}


async def crear_mensaje(
    id_incidente: int,
    id_usuario: int,
    contenido: str,
    nombre_emisor: str,
    rol_emisor: str,
    db: AsyncSession,
) -> MensajeChat:
    msg = MensajeChat(
        id_incidente=id_incidente,
        id_usuario=id_usuario,
        contenido=contenido,
        nombre_emisor=nombre_emisor,
        rol_emisor=rol_emisor,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)

    # A4 - Notificar al destinatario para sincronización inter-rol.
    try:
        await _notificar_destinatarios_chat(
            id_incidente=id_incidente,
            id_emisor=id_usuario,
            rol_emisor=rol_emisor,
            nombre_emisor=nombre_emisor,
            contenido=contenido,
            db=db,
        )
    except Exception as exc:
        logger.warning(f"[Chat] No se pudo notificar el mensaje del incidente {id_incidente}: {exc}")

    return msg


async def _notificar_destinatarios_chat(
    id_incidente: int,
    id_emisor: int,
    rol_emisor: str,
    nombre_emisor: str,
    contenido: str,
    db: AsyncSession,
) -> None:
    """Calcula los destinatarios (cliente y/o taller) y crea/actualiza notificación tipo MENSAJE_CHAT.

    Para no spamear, si ya existe una notificación MENSAJE_CHAT NO leída del mismo incidente
    para ese destinatario, se actualiza el mensaje y la fecha en lugar de crear una nueva."""
    r = await db.execute(select(Incidente).where(Incidente.id_incidente == id_incidente))
    inc = r.scalar_one_or_none()
    if not inc or inc.id_taller is None:
        return

    cliente_user_id: int | None = None
    taller_user_id: int | None = None

    cr = await db.execute(select(Cliente).where(Cliente.id_cliente == inc.id_cliente))
    cliente = cr.scalar_one_or_none()
    if cliente:
        cliente_user_id = cliente.id_usuario

    tr = await db.execute(select(Taller).where(Taller.id_taller == inc.id_taller))
    taller = tr.scalar_one_or_none()
    if taller:
        taller_user_id = taller.id_usuario

    rol_up = (rol_emisor or "").upper()
    destinatarios: list[int] = []
    if rol_up == "CLIENTE" and taller_user_id:
        destinatarios.append(taller_user_id)
    elif rol_up == "TALLER" and cliente_user_id:
        destinatarios.append(cliente_user_id)
    elif rol_up == "ADMINISTRADOR":
        if cliente_user_id and cliente_user_id != id_emisor:
            destinatarios.append(cliente_user_id)
        if taller_user_id and taller_user_id != id_emisor:
            destinatarios.append(taller_user_id)
    else:
        if cliente_user_id and cliente_user_id != id_emisor:
            destinatarios.append(cliente_user_id)
        if taller_user_id and taller_user_id != id_emisor:
            destinatarios.append(taller_user_id)

    preview = (contenido or "").strip().replace("\n", " ")
    if len(preview) > 80:
        preview = preview[:77] + "…"
    titulo = f"Nuevo mensaje — Incidente #{id_incidente}"
    mensaje = f"{nombre_emisor}: {preview}" if preview else f"{nombre_emisor} te envió un mensaje."

    for id_dest in destinatarios:
        if id_dest == id_emisor:
            continue
        existente_r = await db.execute(
            select(Notificacion)
            .where(
                Notificacion.id_usuario == id_dest,
                Notificacion.id_incidente == id_incidente,
                Notificacion.tipo == "MENSAJE_CHAT",
                Notificacion.leida == False,  # noqa: E712
            )
            .order_by(Notificacion.created_at.desc())
            .limit(1)
        )
        existente = existente_r.scalar_one_or_none()
        if existente:
            existente.titulo = titulo
            existente.mensaje = mensaje
            try:
                await db.commit()
            except Exception:
                await db.rollback()
        else:
            await notificacion_service.crear_notificacion(
                db=db,
                id_usuario=id_dest,
                titulo=titulo,
                mensaje=mensaje,
                tipo="MENSAJE_CHAT",
                id_incidente=id_incidente,
            )
