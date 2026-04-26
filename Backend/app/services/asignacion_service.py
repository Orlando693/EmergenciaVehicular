import math
import logging
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.taller import Taller
from app.models.cliente import Cliente
from app.models.incidente import Incidente
from app.schemas.incidente import IncidenteOut
from app.services.incidente_service import obtener_detalle_incidente
from app.services import notificacion_service

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
