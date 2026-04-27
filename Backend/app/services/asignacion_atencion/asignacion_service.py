import math
import logging
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.taller import Taller
from app.models.cliente import Cliente
from app.models.incidente import Incidente, IncidenteHistorial
from app.schemas.incidente import IncidenteOut
from app.services.gestion_incidentes.incidente_service import obtener_detalle_incidente
from app.services.asignacion_atencion import notificacion_service

logger = logging.getLogger(__name__)


def calcular_distancia(lat1, lon1, lat2, lon2) -> float:
    if any(v is None for v in (lat1, lon1, lat2, lon2)):
        return float('inf')
    R = 6371.0
    lat1_r, lon1_r = math.radians(float(lat1)), math.radians(float(lon1))
    lat2_r, lon2_r = math.radians(float(lat2)), math.radians(float(lon2))
    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


async def asignar_taller_optimo(id_incidente: int, db: AsyncSession) -> IncidenteOut:
    # 1. Obtener incidente disponible
    stmt = select(Incidente).where(
        Incidente.id_incidente == id_incidente,
        Incidente.id_taller.is_(None),
        Incidente.estado == "REPORTADO",
    )
    result = await db.execute(stmt)
    incidente = result.scalar_one_or_none()

    if not incidente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incidente no encontrado, o ya fue asignado/procesado.",
        )

    # 2. Talleres disponibles
    res_talleres = await db.execute(select(Taller).where(Taller.estado_registro == "APROBADO"))
    talleres = res_talleres.scalars().all()

    if not talleres:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay talleres disponibles en este momento.",
        )

    # 3. Elegir taller mas cercano
    taller_optimo = min(
        talleres,
        key=lambda t: calcular_distancia(
            incidente.ubicacion_lat, incidente.ubicacion_lng,
            t.latitud, t.longitud,
        ),
    )

    # 4. Asignar y cambiar estado
    incidente.id_taller = taller_optimo.id_taller
    incidente.estado = "EN_PROCESO"
    db.add(incidente)
    await db.commit()
    await db.refresh(incidente)

    # Historial: asignacion de taller
    hist = IncidenteHistorial(
        id_incidente=incidente.id_incidente,
        estado_anterior="REPORTADO",
        estado_nuevo="EN_PROCESO",
        observacion=f"Taller asignado: {taller_optimo.razon_social}. Distancia aprox.: {calcular_distancia(incidente.ubicacion_lat, incidente.ubicacion_lng, taller_optimo.latitud, taller_optimo.longitud):.1f} km."
    )
    db.add(hist)
    await db.commit()

    # 5. Notificar al cliente
    try:
        cliente_r = await db.execute(select(Cliente).where(Cliente.id_cliente == incidente.id_cliente))
        cliente = cliente_r.scalar_one_or_none()
        if cliente:
            await notificacion_service.crear_notificacion(
                db=db,
                id_usuario=cliente.id_usuario,
                titulo=f"Taller asignado — Incidente #{incidente.id_incidente}",
                mensaje=f"Tu incidente fue asignado al taller: {taller_optimo.razon_social}. Pronto se pondran en contacto contigo.",
                tipo="ASIGNACION",
                id_incidente=incidente.id_incidente,
            )
    except Exception as exc:
        logger.warning(f"No se pudo notificar al cliente: {exc}")

    # 6. Notificar al taller
    try:
        await notificacion_service.crear_notificacion(
            db=db,
            id_usuario=taller_optimo.id_usuario,
            titulo=f"Nuevo servicio asignado #{incidente.id_incidente}",
            mensaje=f"Se te asigno un incidente de tipo {incidente.clasificacion_ia or 'vehicular'}. Revisa los detalles en la plataforma.",
            tipo="NUEVO_SERVICIO",
            id_incidente=incidente.id_incidente,
        )
    except Exception as exc:
        logger.warning(f"No se pudo notificar al taller: {exc}")

    return await obtener_detalle_incidente(incidente.id_incidente, 0, es_admin=True, es_taller=False, db=db)


async def _obtener_taller_del_usuario(id_usuario: int, db: AsyncSession) -> Taller:
    res = await db.execute(select(Taller).where(Taller.id_usuario == id_usuario))
    taller = res.scalar_one_or_none()
    if not taller:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes un taller registrado asociado a esta cuenta.",
        )
    if str(taller.estado_registro) not in ("APROBADO", "EstadoTallerEnum.APROBADO"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu taller aún no está APROBADO por el administrador.",
        )
    return taller


async def aceptar_solicitud(id_incidente: int, id_usuario: int, db: AsyncSession) -> IncidenteOut:
    """CU11/CU12 - El Taller acepta directamente una solicitud disponible.
    - Verifica que el taller esté aprobado.
    - Asigna el incidente al taller solo si sigue REPORTADO y sin taller.
    - Cambia estado a EN_PROCESO, registra historial y notifica al cliente."""
    taller = await _obtener_taller_del_usuario(id_usuario, db)

    stmt = select(Incidente).where(Incidente.id_incidente == id_incidente)
    incidente = (await db.execute(stmt)).scalar_one_or_none()

    if not incidente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incidente no encontrado.")
    if incidente.id_taller is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Esta solicitud ya fue tomada por otro taller.")
    if incidente.estado != "REPORTADO":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Esta solicitud ya no está disponible para aceptarse.")

    # Calcular distancia aprox (informativa)
    dist = calcular_distancia(
        incidente.ubicacion_lat, incidente.ubicacion_lng,
        taller.latitud, taller.longitud,
    )
    dist_str = f" Distancia aprox.: {dist:.1f} km." if dist != float('inf') else ""

    incidente.id_taller = taller.id_taller
    incidente.estado = "EN_PROCESO"
    db.add(incidente)

    hist = IncidenteHistorial(
        id_incidente=incidente.id_incidente,
        estado_anterior="REPORTADO",
        estado_nuevo="EN_PROCESO",
        observacion=f"Solicitud aceptada por el taller '{taller.razon_social}'.{dist_str}"
    )
    db.add(hist)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No se pudo aceptar la solicitud.")

    # Notificar al cliente
    try:
        cliente_r = await db.execute(select(Cliente).where(Cliente.id_cliente == incidente.id_cliente))
        cliente = cliente_r.scalar_one_or_none()
        if cliente:
            await notificacion_service.crear_notificacion(
                db=db,
                id_usuario=cliente.id_usuario,
                titulo=f"Taller asignado — Incidente #{incidente.id_incidente}",
                mensaje=f"El taller '{taller.razon_social}' aceptó tu solicitud y ya está en camino.",
                tipo="ASIGNACION",
                id_incidente=incidente.id_incidente,
            )
    except Exception as exc:
        logger.warning(f"No se pudo notificar al cliente al aceptar solicitud: {exc}")

    return await obtener_detalle_incidente(incidente.id_incidente, 0, es_admin=True, es_taller=False, db=db)


async def rechazar_solicitud(
    id_incidente: int,
    id_usuario: int,
    observacion: str | None,
    db: AsyncSession,
) -> dict:
    """CU11 - El Taller rechaza una solicitud disponible.
    - Solo registra historial; el incidente sigue REPORTADO y disponible para otros.
    - No elimina ni modifica datos del cliente."""
    taller = await _obtener_taller_del_usuario(id_usuario, db)

    stmt = select(Incidente).where(Incidente.id_incidente == id_incidente)
    incidente = (await db.execute(stmt)).scalar_one_or_none()

    if not incidente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incidente no encontrado.")

    if incidente.estado in ("RESUELTO", "PAGADO", "CANCELADO"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No puedes rechazar una solicitud ya finalizada.")

    if incidente.id_taller is not None and incidente.id_taller != taller.id_taller:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Esta solicitud ya está asignada a otro taller.")

    nota = (observacion or "Sin observación").strip()
    hist = IncidenteHistorial(
        id_incidente=incidente.id_incidente,
        estado_anterior=incidente.estado,
        estado_nuevo=incidente.estado,
        observacion=f"Solicitud rechazada por el taller '{taller.razon_social}'. Motivo: {nota}",
    )
    db.add(hist)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No se pudo registrar el rechazo.")

    # Notificar al cliente que un taller rechazó (informativo, sin alarma).
    try:
        cliente_r = await db.execute(select(Cliente).where(Cliente.id_cliente == incidente.id_cliente))
        cliente = cliente_r.scalar_one_or_none()
        if cliente:
            await notificacion_service.crear_notificacion(
                db=db,
                id_usuario=cliente.id_usuario,
                titulo=f"Buscando taller — Incidente #{incidente.id_incidente}",
                mensaje=f"Un taller no pudo tomar tu caso. Seguimos buscando otro disponible.",
                tipo="ESTADO_CAMBIO",
                id_incidente=incidente.id_incidente,
            )
    except Exception as exc:
        logger.warning(f"No se pudo notificar al cliente al rechazar solicitud: {exc}")

    return {"detail": "Solicitud rechazada. Sigue disponible para otros talleres."}
