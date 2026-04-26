from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status

from app.models.mensaje_chat import MensajeChat
from app.models.incidente import Incidente
from app.models.cliente import Cliente
from app.models.taller import Taller


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
    return msg
