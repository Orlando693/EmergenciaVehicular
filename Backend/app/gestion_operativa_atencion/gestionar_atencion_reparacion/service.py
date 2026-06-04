from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.administracion.usuarios.model import Cliente, Usuario
from app.asignacion_atencion.notificaciones import service as notificacion_service
from app.bitacora_reportes.bitacora.model import Bitacora
from app.gestion_incidentes.incidentes.model import Incidente, IncidenteHistorial
from app.gestion_operativa_atencion.atencion_tiempo_real.manager import atencion_realtime_manager
from app.gestion_operativa_atencion.gestionar_atencion_reparacion.model import EstimacionAtencion
from app.gestion_operativa_atencion.gestionar_atencion_reparacion.schemas import (
    EstimacionAtencionCreate,
    EstimacionAtencionOut,
    EstimacionAtencionUpdate,
)
from app.operaciones.talleres.model import Taller


# ── Helpers privados ──────────────────────────────────────────────────────────

async def _get_taller(db: AsyncSession, usuario: Usuario) -> Taller:
    result = await db.execute(
        select(Taller).where(
            Taller.id_usuario == usuario.id_usuario,
            Taller.id_tenant == usuario.id_tenant,
        )
    )
    taller = result.scalar_one_or_none()
    if not taller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil de taller no encontrado para este usuario",
        )
    return taller


async def _get_incidente_asignado(
    db: AsyncSession,
    id_incidente: int,
    id_taller: int,
    id_tenant: int,
) -> Incidente:
    result = await db.execute(
        select(Incidente)
        .where(
            Incidente.id_incidente == id_incidente,
            Incidente.id_taller == id_taller,
            Incidente.id_tenant == id_tenant,
        )
        .options(selectinload(Incidente.cliente))
    )
    incidente = result.scalar_one_or_none()
    if not incidente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Servicio no encontrado o no asignado a este taller",
        )
    return incidente


async def _get_id_usuario_cliente(db: AsyncSession, id_cliente: int) -> int | None:
    result = await db.execute(
        select(Cliente.id_usuario).where(Cliente.id_cliente == id_cliente)
    )
    return result.scalar_one_or_none()


async def _registrar_historial(
    db: AsyncSession,
    incidente: Incidente,
    observacion: str,
) -> None:
    db.add(
        IncidenteHistorial(
            id_tenant=incidente.id_tenant,
            id_incidente=incidente.id_incidente,
            estado_anterior=incidente.estado,
            estado_nuevo=incidente.estado,
            observacion=observacion,
        )
    )


async def _registrar_bitacora(
    db: AsyncSession,
    usuario: Usuario,
    id_incidente: int,
    accion: str,
) -> None:
    db.add(
        Bitacora(
            id_tenant=usuario.id_tenant,
            modulo="CU22 Gestionar estimación de atención y reparación",
            accion=accion,
            rol="TALLER",
            usuario_email=usuario.email,
            id_usuario=usuario.id_usuario,
        )
    )


def _to_out(estimacion: EstimacionAtencion) -> EstimacionAtencionOut:
    taller_nombre = estimacion.taller.razon_social if estimacion.taller else None
    return EstimacionAtencionOut(
        id_estimacion=estimacion.id_estimacion,
        id_incidente=estimacion.id_incidente,
        id_taller=estimacion.id_taller,
        tiempo_llegada=estimacion.tiempo_llegada,
        tiempo_reparacion=estimacion.tiempo_reparacion,
        observacion=estimacion.observacion,
        taller_nombre=taller_nombre,
        created_at=estimacion.created_at,
        updated_at=estimacion.updated_at,
    )


# ── Casos de uso públicos ─────────────────────────────────────────────────────

async def registrar_estimacion(
    db: AsyncSession,
    id_incidente: int,
    data: EstimacionAtencionCreate,
    usuario: Usuario,
) -> EstimacionAtencionOut:
    """
    Pasos 4-7 del flujo: el taller registra por primera vez las estimaciones
    de llegada y reparación para el incidente asignado.
    """
    taller = await _get_taller(db, usuario)
    incidente = await _get_incidente_asignado(db, id_incidente, taller.id_taller, usuario.id_tenant)

    # Verificar que no exista ya una estimación para este incidente
    existente = await db.execute(
        select(EstimacionAtencion).where(
            EstimacionAtencion.id_incidente == id_incidente,
            EstimacionAtencion.id_tenant == usuario.id_tenant,
        )
    )
    if existente.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una estimación para este incidente. Usa el endpoint de actualización.",
        )

    estimacion = EstimacionAtencion(
        id_tenant=usuario.id_tenant,
        id_incidente=id_incidente,
        id_taller=taller.id_taller,
        tiempo_llegada=data.tiempo_llegada,
        tiempo_reparacion=data.tiempo_reparacion,
        observacion=data.observacion,
    )
    db.add(estimacion)

    obs = (
        f"Taller '{taller.razon_social}' registró estimación: "
        f"llegada={data.tiempo_llegada or 'N/A'}, reparación={data.tiempo_reparacion or 'N/A'}"
    )
    await _registrar_historial(db, incidente, obs)
    await _registrar_bitacora(db, usuario, id_incidente, obs)

    await db.commit()
    await db.refresh(estimacion)

    # Cargar relación taller para la respuesta
    result = await db.execute(
        select(EstimacionAtencion)
        .where(EstimacionAtencion.id_estimacion == estimacion.id_estimacion)
        .options(selectinload(EstimacionAtencion.taller))
    )
    estimacion = result.scalar_one()

    # Notificar al cliente (paso 8: cliente visualiza el tiempo estimado)
    await _notificar_y_broadcast(db, incidente, taller, estimacion, usuario, es_actualizacion=False)

    return _to_out(estimacion)


async def actualizar_estimacion(
    db: AsyncSession,
    id_incidente: int,
    data: EstimacionAtencionUpdate,
    usuario: Usuario,
) -> EstimacionAtencionOut:
    """
    Paso 9-11 del flujo: el taller actualiza la estimación cuando hay cambios
    durante la atención. Notifica al cliente y registra en bitácora.
    """
    taller = await _get_taller(db, usuario)
    incidente = await _get_incidente_asignado(db, id_incidente, taller.id_taller, usuario.id_tenant)

    result = await db.execute(
        select(EstimacionAtencion)
        .where(
            EstimacionAtencion.id_incidente == id_incidente,
            EstimacionAtencion.id_tenant == usuario.id_tenant,
        )
        .options(selectinload(EstimacionAtencion.taller))
    )
    estimacion = result.scalar_one_or_none()
    if not estimacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe estimación previa. Registra primero la estimación.",
        )

    cambios: list[str] = []
    if data.tiempo_llegada is not None:
        if data.tiempo_llegada != estimacion.tiempo_llegada:
            cambios.append(f"llegada: '{estimacion.tiempo_llegada}' → '{data.tiempo_llegada}'")
        estimacion.tiempo_llegada = data.tiempo_llegada
    if data.tiempo_reparacion is not None:
        if data.tiempo_reparacion != estimacion.tiempo_reparacion:
            cambios.append(f"reparación: '{estimacion.tiempo_reparacion}' → '{data.tiempo_reparacion}'")
        estimacion.tiempo_reparacion = data.tiempo_reparacion
    if data.observacion is not None:
        estimacion.observacion = data.observacion

    obs = (
        f"Taller '{taller.razon_social}' actualizó estimación en incidente #{id_incidente}. "
        + ("; ".join(cambios) if cambios else "Observación actualizada")
    )
    await _registrar_historial(db, incidente, obs)
    await _registrar_bitacora(db, usuario, id_incidente, obs)

    await db.commit()
    await db.refresh(estimacion)

    # Notificar al cliente (paso 10)
    await _notificar_y_broadcast(db, incidente, taller, estimacion, usuario, es_actualizacion=True)

    return _to_out(estimacion)


async def obtener_estimacion(
    db: AsyncSession,
    id_incidente: int,
    usuario: Usuario,
) -> EstimacionAtencionOut:
    """
    Devuelve la estimación vigente del incidente.
    Accesible para TALLER (dueño del incidente) y CLIENTE (dueño del incidente).
    """
    # Determinar si el usuario es taller o cliente y validar acceso
    roles = [r.nombre for r in usuario.roles] if usuario.roles else []
    id_incidente_verificado = await _verificar_acceso_lectura(db, id_incidente, usuario, roles)

    result = await db.execute(
        select(EstimacionAtencion)
        .where(
            EstimacionAtencion.id_incidente == id_incidente_verificado,
            EstimacionAtencion.id_tenant == usuario.id_tenant,
        )
        .options(selectinload(EstimacionAtencion.taller))
    )
    estimacion = result.scalar_one_or_none()
    if not estimacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe estimación registrada para este incidente",
        )
    return _to_out(estimacion)


# ── Auxiliares internos ───────────────────────────────────────────────────────

async def _verificar_acceso_lectura(
    db: AsyncSession,
    id_incidente: int,
    usuario: Usuario,
    roles: list[str],
) -> int:
    """Devuelve id_incidente si el usuario tiene acceso (TALLER asignado o CLIENTE dueño)."""
    if "TALLER" in roles:
        taller = await _get_taller(db, usuario)
        r = await db.execute(
            select(Incidente.id_incidente).where(
                Incidente.id_incidente == id_incidente,
                Incidente.id_taller == taller.id_taller,
                Incidente.id_tenant == usuario.id_tenant,
            )
        )
    else:
        # CLIENTE
        r = await db.execute(
            select(Incidente.id_incidente)
            .join(Cliente, Cliente.id_cliente == Incidente.id_cliente)
            .where(
                Incidente.id_incidente == id_incidente,
                Cliente.id_usuario == usuario.id_usuario,
                Incidente.id_tenant == usuario.id_tenant,
            )
        )
    val = r.scalar_one_or_none()
    if not val:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Servicio no encontrado o sin acceso",
        )
    return val


async def _notificar_y_broadcast(
    db: AsyncSession,
    incidente: Incidente,
    taller: Taller,
    estimacion: EstimacionAtencion,
    usuario: Usuario,
    es_actualizacion: bool,
) -> None:
    accion = "actualización de" if es_actualizacion else "nuevas"
    titulo = f"{'Actualización de estimación' if es_actualizacion else 'Estimación disponible'}"
    partes: list[str] = []
    if estimacion.tiempo_llegada:
        partes.append(f"Tiempo de llegada: {estimacion.tiempo_llegada}")
    if estimacion.tiempo_reparacion:
        partes.append(f"Tiempo de reparación: {estimacion.tiempo_reparacion}")
    mensaje = (
        f"El taller '{taller.razon_social}' informó {accion} estimaciones. "
        + " | ".join(partes)
    )

    id_usuario_cliente = await _get_id_usuario_cliente(db, incidente.id_cliente)
    if id_usuario_cliente:
        try:
            await notificacion_service.crear_notificacion(
                db=db,
                id_usuario=id_usuario_cliente,
                titulo=titulo,
                mensaje=mensaje,
                tipo="ESTIMACION_ATENCION",
                id_incidente=incidente.id_incidente,
                id_tenant=usuario.id_tenant,
            )
        except Exception:
            pass

    try:
        await atencion_realtime_manager.broadcast(
            incidente.id_incidente,
            {
                "tipo": "ESTIMACION_ATENCION",
                "accion": "ACTUALIZADA" if es_actualizacion else "REGISTRADA",
                "id_incidente": incidente.id_incidente,
                "id_taller": taller.id_taller,
                "taller_nombre": taller.razon_social,
                "tiempo_llegada": estimacion.tiempo_llegada,
                "tiempo_reparacion": estimacion.tiempo_reparacion,
                "observacion": estimacion.observacion,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )
    except Exception:
        pass
