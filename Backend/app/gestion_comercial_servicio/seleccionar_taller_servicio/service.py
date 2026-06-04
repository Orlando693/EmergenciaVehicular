from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.administracion.usuarios.model import Cliente, Usuario
from app.bitacora_reportes.bitacora.model import Bitacora
from app.core.enums import EstadoTallerEnum
from app.gestion_incidentes.incidentes.model import Incidente, IncidenteHistorial
from app.gestion_operativa_atencion.cotizaciones.model import CotizacionReparacion
from app.gestion_operativa_atencion.atencion_tiempo_real.manager import atencion_realtime_manager
from app.operaciones.talleres.model import Taller
from app.asignacion_atencion.notificaciones import service as notificacion_service
from app.gestion_comercial_servicio.seleccionar_taller_servicio.schemas import (
    CotizacionComparacionOut,
    SeleccionTallerOut,
)


# ── Helpers privados ──────────────────────────────────────────────────────────

async def _get_cliente(db: AsyncSession, usuario: Usuario) -> Cliente:
    result = await db.execute(
        select(Cliente).where(
            Cliente.id_usuario == usuario.id_usuario,
            Cliente.id_tenant == usuario.id_tenant,
        )
    )
    cliente = result.scalar_one_or_none()
    if not cliente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de cliente no encontrado")
    return cliente


async def _get_incidente_del_cliente(
    db: AsyncSession,
    id_incidente: int,
    id_cliente: int,
    id_tenant: int,
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


async def _registrar_historial(
    db: AsyncSession,
    incidente: Incidente,
    estado_anterior: str | None,
    estado_nuevo: str,
    observacion: str,
) -> None:
    db.add(
        IncidenteHistorial(
            id_tenant=incidente.id_tenant,
            id_incidente=incidente.id_incidente,
            estado_anterior=estado_anterior,
            estado_nuevo=estado_nuevo,
            observacion=observacion,
        )
    )


async def _registrar_bitacora(
    db: AsyncSession,
    usuario: Usuario,
    id_incidente: int,
    id_taller: int,
    id_cotizacion: int,
) -> None:
    db.add(
        Bitacora(
            id_tenant=usuario.id_tenant,
            modulo="CU21 Seleccionar taller para el servicio",
            accion=(
                f"Cliente selecciono taller #{id_taller} "
                f"via cotizacion #{id_cotizacion} para incidente #{id_incidente}"
            ),
            rol="CLIENTE",
            usuario_email=usuario.email,
            id_usuario=usuario.id_usuario,
        )
    )


# ── Casos de uso públicos ─────────────────────────────────────────────────────

async def listar_cotizaciones_para_seleccion(
    db: AsyncSession,
    id_incidente: int,
    usuario: Usuario,
) -> list[CotizacionComparacionOut]:
    """
    Paso 3-5 del flujo: muestra cotizaciones RESPONDIDAS del incidente
    del cliente para que pueda compararlas.
    """
    cliente = await _get_cliente(db, usuario)
    incidente = await _get_incidente_del_cliente(db, id_incidente, cliente.id_cliente, usuario.id_tenant)

    result = await db.execute(
        select(CotizacionReparacion)
        .where(
            CotizacionReparacion.id_incidente == incidente.id_incidente,
            CotizacionReparacion.id_tenant == usuario.id_tenant,
            CotizacionReparacion.estado.in_(["RESPONDIDA", "ACEPTADA"]),
        )
        .options(
            selectinload(CotizacionReparacion.taller),
        )
        .order_by(CotizacionReparacion.precio_estimado.asc().nullslast())
    )
    cotizaciones = result.scalars().all()

    if not cotizaciones:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay cotizaciones disponibles para este incidente. "
                   "El taller aún no ha respondido o no se ha solicitado cotización.",
        )

    return [_enriquecer_cotizacion(c) for c in cotizaciones]


async def seleccionar_taller(
    db: AsyncSession,
    id_incidente: int,
    id_cotizacion: int,
    usuario: Usuario,
) -> SeleccionTallerOut:
    """
    Pasos 6-11 del flujo: el cliente elige una cotización.
    - Valida disponibilidad de cotización y taller.
    - Acepta la cotización seleccionada y rechaza las demás.
    - Asigna el taller al incidente y actualiza el estado.
    - Notifica al taller y registra en bitácora.
    """
    cliente = await _get_cliente(db, usuario)
    incidente = await _get_incidente_del_cliente(db, id_incidente, cliente.id_cliente, usuario.id_tenant)

    # Paso 7 – Validar que la cotización siga disponible (RESPONDIDA)
    cot_result = await db.execute(
        select(CotizacionReparacion)
        .where(
            CotizacionReparacion.id_cotizacion == id_cotizacion,
            CotizacionReparacion.id_incidente == incidente.id_incidente,
            CotizacionReparacion.id_tenant == usuario.id_tenant,
        )
        .options(selectinload(CotizacionReparacion.taller))
    )
    cotizacion = cot_result.scalar_one_or_none()

    if not cotizacion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cotización no encontrada")

    if cotizacion.estado == "ACEPTADA":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esta cotización ya fue aceptada previamente",
        )
    if cotizacion.estado != "RESPONDIDA":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cotización seleccionada ya no está disponible. Selecciona otra opción.",
        )

    # Validar que el taller sigue APROBADO
    taller_result = await db.execute(
        select(Taller).where(
            Taller.id_taller == cotizacion.id_taller,
            Taller.id_tenant == usuario.id_tenant,
        )
    )
    taller = taller_result.scalar_one_or_none()
    if not taller or taller.estado_registro != EstadoTallerEnum.APROBADO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El taller seleccionado ya no está disponible. Selecciona otra opción.",
        )

    # Paso 8 – Registrar taller en el incidente
    estado_anterior = incidente.estado
    incidente.id_taller = cotizacion.id_taller
    incidente.estado = "EN_PROCESO"

    # Paso 9 – Actualizar cotizaciones: aceptar seleccionada, rechazar las demás
    cotizacion.estado = "ACEPTADA"

    otras_result = await db.execute(
        select(CotizacionReparacion).where(
            CotizacionReparacion.id_incidente == incidente.id_incidente,
            CotizacionReparacion.id_tenant == usuario.id_tenant,
            CotizacionReparacion.id_cotizacion != id_cotizacion,
            CotizacionReparacion.estado == "RESPONDIDA",
        )
    )
    otras = otras_result.scalars().all()
    for otra in otras:
        otra.estado = "RECHAZADA"

    # Registrar historial del incidente
    obs = f"Cliente seleccionó taller {taller.razon_social} mediante cotización #{id_cotizacion}"
    await _registrar_historial(db, incidente, estado_anterior, "EN_PROCESO", obs)

    # Paso 11 – Bitácora
    await _registrar_bitacora(db, usuario, incidente.id_incidente, taller.id_taller, id_cotizacion)

    await db.commit()
    await db.refresh(incidente)

    # Paso 10 – Notificar al taller seleccionado
    try:
        await notificacion_service.crear_notificacion(
            db=db,
            id_usuario=taller.id_usuario,
            titulo="Taller seleccionado para servicio",
            mensaje=(
                f"El cliente eligió tu taller para atender el incidente #{incidente.id_incidente}. "
                f"Cotización #{id_cotizacion} aceptada."
            ),
            tipo="TALLER_SELECCIONADO",
            id_incidente=incidente.id_incidente,
            id_tenant=usuario.id_tenant,
        )
    except Exception:
        pass

    # Broadcast WebSocket a la sala del incidente
    try:
        await atencion_realtime_manager.broadcast(
            incidente.id_incidente,
            {
                "tipo": "TALLER_SELECCIONADO",
                "id_incidente": incidente.id_incidente,
                "id_taller": taller.id_taller,
                "taller_nombre": taller.razon_social,
                "id_cotizacion": id_cotizacion,
                "estado": incidente.estado,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )
    except Exception:
        pass

    return SeleccionTallerOut(
        id_incidente=incidente.id_incidente,
        id_taller=taller.id_taller,
        id_cotizacion_aceptada=id_cotizacion,
        taller_nombre=taller.razon_social,
        taller_direccion=taller.direccion,
        estado_incidente=incidente.estado,
        cotizaciones_rechazadas=len(otras),
        mensaje=(
            f"Taller '{taller.razon_social}' seleccionado correctamente. "
            f"El incidente avanza a estado EN_PROCESO."
        ),
    )


async def obtener_seleccion_actual(
    db: AsyncSession,
    id_incidente: int,
    usuario: Usuario,
) -> SeleccionTallerOut | None:
    """
    Devuelve la cotización ACEPTADA actual (si el cliente ya eligió un taller).
    """
    cliente = await _get_cliente(db, usuario)
    incidente = await _get_incidente_del_cliente(db, id_incidente, cliente.id_cliente, usuario.id_tenant)

    result = await db.execute(
        select(CotizacionReparacion)
        .where(
            CotizacionReparacion.id_incidente == incidente.id_incidente,
            CotizacionReparacion.id_tenant == usuario.id_tenant,
            CotizacionReparacion.estado == "ACEPTADA",
        )
        .options(selectinload(CotizacionReparacion.taller))
    )
    cotizacion = result.scalar_one_or_none()

    if not cotizacion:
        return None

    taller = cotizacion.taller
    return SeleccionTallerOut(
        id_incidente=incidente.id_incidente,
        id_taller=cotizacion.id_taller,
        id_cotizacion_aceptada=cotizacion.id_cotizacion,
        taller_nombre=taller.razon_social if taller else None,
        taller_direccion=taller.direccion if taller else None,
        estado_incidente=incidente.estado,
        mensaje="Taller ya seleccionado para este incidente.",
    )


# ── Helper de enriquecimiento ─────────────────────────────────────────────────

def _enriquecer_cotizacion(c: CotizacionReparacion) -> CotizacionComparacionOut:
    taller = c.taller
    return CotizacionComparacionOut(
        id_cotizacion=c.id_cotizacion,
        id_incidente=c.id_incidente,
        id_taller=c.id_taller,
        taller_nombre=taller.razon_social if taller else None,
        taller_direccion=taller.direccion if taller else None,
        taller_calificacion=taller.calificacion_promedio if taller else None,
        taller_acepta_remolque=taller.acepta_remolque if taller else False,
        descripcion_solicitud=c.descripcion_solicitud,
        precio_estimado=c.precio_estimado,
        detalle_danio=c.detalle_danio,
        condiciones_servicio=c.condiciones_servicio,
        tiempo_estimado=c.tiempo_estimado,
        estado=c.estado,
        respuesta_at=c.respuesta_at,
        created_at=c.created_at,
    )
