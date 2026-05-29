from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.bitacora import Bitacora
from app.models.cliente import Cliente
from app.models.cotizacion_reparacion import CotizacionReparacion
from app.models.incidente import Incidente
from app.models.taller import Taller
from app.models.usuario import Usuario
from app.schemas.atencion_tiempo_real import (
    CotizacionReparacionOut,
    CotizacionRespuestaUpdate,
    CotizacionSolicitudCreate,
)
from app.services.asignacion_atencion import notificacion_service


def _roles(usuario: Usuario) -> set[str]:
    return {rol.nombre.upper() for rol in getattr(usuario, "roles", [])}


async def solicitar_cotizacion(
    db: AsyncSession,
    usuario: Usuario,
    payload: CotizacionSolicitudCreate,
) -> CotizacionReparacionOut:
    cliente = await _cliente_del_usuario(db, usuario)
    if not cliente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")

    incidente = await _incidente_del_cliente(db, usuario.id_tenant, cliente.id_cliente, payload.id_incidente)
    if not incidente.id_taller:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El incidente no tiene taller asignado para solicitar cotizacion",
        )

    existente = await _cotizacion_por_incidente_taller(db, usuario.id_tenant, incidente.id_incidente, incidente.id_taller)
    if existente:
        return _cotizacion_out(existente)

    cotizacion = CotizacionReparacion(
        id_tenant=usuario.id_tenant,
        id_incidente=incidente.id_incidente,
        id_cliente=cliente.id_cliente,
        id_taller=incidente.id_taller,
        descripcion_solicitud=payload.descripcion_solicitud,
        estado="PENDIENTE",
    )
    db.add(cotizacion)
    await _registrar_bitacora(db, usuario, f"Solicito cotizacion para incidente #{incidente.id_incidente}")
    await db.commit()
    await db.refresh(cotizacion)

    await _notificar_taller(db, usuario.id_tenant, cotizacion)
    return await obtener_cotizacion(db, usuario, cotizacion.id_cotizacion)


async def responder_cotizacion(
    db: AsyncSession,
    usuario: Usuario,
    id_cotizacion: int,
    payload: CotizacionRespuestaUpdate,
) -> CotizacionReparacionOut:
    taller = await _taller_del_usuario(db, usuario)
    if not taller:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado o no es un taller valido")

    cotizacion = await _cotizacion_por_id(db, usuario.id_tenant, id_cotizacion)
    if not cotizacion or cotizacion.id_taller != taller.id_taller:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cotizacion no encontrada")

    cotizacion.precio_estimado = payload.precio_estimado
    cotizacion.detalle_danio = payload.detalle_danio
    cotizacion.condiciones_servicio = payload.condiciones_servicio
    cotizacion.tiempo_estimado = payload.tiempo_estimado
    cotizacion.estado = "RESPONDIDA"
    cotizacion.respuesta_at = datetime.utcnow()

    await _registrar_bitacora(db, usuario, f"Respondio cotizacion #{cotizacion.id_cotizacion}")
    await db.commit()
    await db.refresh(cotizacion)

    await _notificar_cliente(db, usuario.id_tenant, cotizacion)
    return await obtener_cotizacion(db, usuario, cotizacion.id_cotizacion)


async def listar_cotizaciones(db: AsyncSession, usuario: Usuario) -> list[CotizacionReparacionOut]:
    stmt = (
        select(CotizacionReparacion)
        .where(CotizacionReparacion.id_tenant == usuario.id_tenant)
        .options(
            selectinload(CotizacionReparacion.taller),
            selectinload(CotizacionReparacion.incidente),
        )
        .order_by(CotizacionReparacion.created_at.desc())
    )

    roles = _roles(usuario)
    if "CLIENTE" in roles:
        cliente = await _cliente_del_usuario(db, usuario)
        if not cliente:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")
        stmt = stmt.where(CotizacionReparacion.id_cliente == cliente.id_cliente)
    elif "TALLER" in roles:
        taller = await _taller_del_usuario(db, usuario)
        if not taller:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Taller no encontrado")
        stmt = stmt.where(CotizacionReparacion.id_taller == taller.id_taller)
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Rol no autorizado para CU20")

    result = await db.execute(stmt)
    return [_cotizacion_out(item) for item in result.scalars().all()]


async def obtener_cotizacion(db: AsyncSession, usuario: Usuario, id_cotizacion: int) -> CotizacionReparacionOut:
    cotizacion = await _cotizacion_por_id(db, usuario.id_tenant, id_cotizacion)
    if not cotizacion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cotizacion no encontrada")

    roles = _roles(usuario)
    if "CLIENTE" in roles:
        cliente = await _cliente_del_usuario(db, usuario)
        if not cliente or cotizacion.id_cliente != cliente.id_cliente:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cotizacion no encontrada")
    elif "TALLER" in roles:
        taller = await _taller_del_usuario(db, usuario)
        if not taller or cotizacion.id_taller != taller.id_taller:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cotizacion no encontrada")
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Rol no autorizado para CU20")

    return _cotizacion_out(cotizacion)


async def _cliente_del_usuario(db: AsyncSession, usuario: Usuario) -> Cliente | None:
    result = await db.execute(
        select(Cliente).where(
            Cliente.id_usuario == usuario.id_usuario,
            Cliente.id_tenant == usuario.id_tenant,
        )
    )
    return result.scalar_one_or_none()


async def _taller_del_usuario(db: AsyncSession, usuario: Usuario) -> Taller | None:
    result = await db.execute(
        select(Taller).where(
            Taller.id_usuario == usuario.id_usuario,
            Taller.id_tenant == usuario.id_tenant,
        )
    )
    return result.scalar_one_or_none()


async def _incidente_del_cliente(
    db: AsyncSession,
    id_tenant: int,
    id_cliente: int,
    id_incidente: int,
) -> Incidente:
    result = await db.execute(
        select(Incidente)
        .where(
            Incidente.id_incidente == id_incidente,
            Incidente.id_cliente == id_cliente,
            Incidente.id_tenant == id_tenant,
        )
        .options(selectinload(Incidente.taller))
    )
    incidente = result.scalar_one_or_none()
    if not incidente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Emergencia vehicular no encontrada")
    return incidente


async def _cotizacion_por_incidente_taller(
    db: AsyncSession,
    id_tenant: int,
    id_incidente: int,
    id_taller: int,
) -> CotizacionReparacion | None:
    result = await db.execute(
        select(CotizacionReparacion)
        .where(
            CotizacionReparacion.id_tenant == id_tenant,
            CotizacionReparacion.id_incidente == id_incidente,
            CotizacionReparacion.id_taller == id_taller,
        )
        .options(
            selectinload(CotizacionReparacion.taller),
            selectinload(CotizacionReparacion.incidente),
        )
    )
    return result.scalar_one_or_none()


async def _cotizacion_por_id(db: AsyncSession, id_tenant: int, id_cotizacion: int) -> CotizacionReparacion | None:
    result = await db.execute(
        select(CotizacionReparacion)
        .where(
            CotizacionReparacion.id_cotizacion == id_cotizacion,
            CotizacionReparacion.id_tenant == id_tenant,
        )
        .options(
            selectinload(CotizacionReparacion.taller),
            selectinload(CotizacionReparacion.incidente),
        )
    )
    return result.scalar_one_or_none()


async def _registrar_bitacora(db: AsyncSession, usuario: Usuario, accion: str) -> None:
    rol = next(iter(_roles(usuario)), "DESCONOCIDO")
    db.add(
        Bitacora(
            id_tenant=usuario.id_tenant,
            modulo="CU20 Cotizaciones de reparacion",
            accion=accion,
            rol=rol,
            usuario_email=usuario.email,
            id_usuario=usuario.id_usuario,
        )
    )


async def _notificar_taller(db: AsyncSession, id_tenant: int, cotizacion: CotizacionReparacion) -> None:
    taller_r = await db.execute(
        select(Taller).where(Taller.id_taller == cotizacion.id_taller, Taller.id_tenant == id_tenant)
    )
    taller = taller_r.scalar_one_or_none()
    if not taller:
        return

    try:
        await notificacion_service.crear_notificacion(
            db=db,
            id_usuario=taller.id_usuario,
            titulo="Nueva solicitud de cotizacion",
            mensaje=f"El cliente solicito una cotizacion para el incidente #{cotizacion.id_incidente}.",
            tipo="COTIZACION_SOLICITADA",
            id_incidente=cotizacion.id_incidente,
            id_tenant=id_tenant,
        )
    except Exception:
        pass


async def _notificar_cliente(db: AsyncSession, id_tenant: int, cotizacion: CotizacionReparacion) -> None:
    cliente_r = await db.execute(
        select(Cliente).where(Cliente.id_cliente == cotizacion.id_cliente, Cliente.id_tenant == id_tenant)
    )
    cliente = cliente_r.scalar_one_or_none()
    if not cliente:
        return

    try:
        await notificacion_service.crear_notificacion(
            db=db,
            id_usuario=cliente.id_usuario,
            titulo="Cotizacion respondida",
            mensaje=f"El taller respondio la cotizacion del incidente #{cotizacion.id_incidente}.",
            tipo="COTIZACION_RESPONDIDA",
            id_incidente=cotizacion.id_incidente,
            id_tenant=id_tenant,
        )
    except Exception:
        pass


def _cotizacion_out(cotizacion: CotizacionReparacion) -> CotizacionReparacionOut:
    data = CotizacionReparacionOut.model_validate(cotizacion)
    if cotizacion.taller:
        data.taller_nombre = cotizacion.taller.razon_social
    if cotizacion.incidente:
        data.incidente_estado = cotizacion.incidente.estado
    return data
