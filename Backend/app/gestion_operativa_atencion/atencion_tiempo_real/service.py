from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.bitacora_reportes.bitacora.model import Bitacora
from app.administracion.usuarios.model import Cliente, Usuario
from app.gestion_incidentes.incidentes.model import Incidente, IncidenteHistorial
from app.operaciones.talleres.model import Taller
from app.gestion_operativa_atencion.atencion_tiempo_real.schemas import (
    AtencionEventoOut,
    AtencionSeguimientoOut,
    TallerSeguimientoOut,
    UbicacionTecnicoIn,
    UbicacionTecnicoOut,
)
from app.gestion_incidentes.incidentes.schemas import IncidenteHistorialOut, IncidenteOut
from app.asignacion_atencion.notificaciones import service as notificacion_service
from app.gestion_operativa_atencion.atencion_tiempo_real.manager import atencion_realtime_manager


ESTADOS_PERMITIDOS = {"EN_PROCESO", "RESUELTO", "CANCELADO"}


def _roles(usuario: Usuario) -> set[str]:
    return {rol.nombre.upper() for rol in getattr(usuario, "roles", [])}


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


async def obtener_incidente_accesible(
    db: AsyncSession,
    id_incidente: int,
    usuario: Usuario,
    exigir_asignado: bool = True,
) -> Incidente:
    result = await db.execute(
        select(Incidente)
        .where(
            Incidente.id_incidente == id_incidente,
            Incidente.id_tenant == usuario.id_tenant,
        )
        .options(
            selectinload(Incidente.taller),
            selectinload(Incidente.vehiculo),
        )
    )
    incidente = result.scalar_one_or_none()
    if not incidente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incidente no encontrado")
    if exigir_asignado and incidente.id_taller is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El incidente no tiene taller asignado para atencion en tiempo real",
        )

    roles = _roles(usuario)
    if "CLIENTE" in roles:
        cliente = await _cliente_del_usuario(db, usuario)
        if not cliente or cliente.id_cliente != incidente.id_cliente:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado para este incidente")
        return incidente

    if "TALLER" in roles:
        taller = await _taller_del_usuario(db, usuario)
        if not taller or incidente.id_taller != taller.id_taller:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado para esta atencion")
        return incidente

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Rol no autorizado para CU18")


async def obtener_seguimiento(db: AsyncSession, id_incidente: int, usuario: Usuario) -> AtencionSeguimientoOut:
    incidente = await obtener_incidente_accesible(db, id_incidente, usuario)
    historial = await _historial(db, incidente)
    inc_out = _incidente_out(incidente)
    taller_out = TallerSeguimientoOut.model_validate(incidente.taller) if incidente.taller else None
    ubicacion = _ubicacion_out(atencion_realtime_manager.get_location(id_incidente))
    return AtencionSeguimientoOut(
        incidente=inc_out,
        taller=taller_out,
        ubicacion_tecnico=ubicacion,
        historial=historial,
        participantes_en_linea=atencion_realtime_manager.participantes_en_linea(id_incidente),
    )


async def actualizar_ubicacion_tecnico(
    db: AsyncSession,
    id_incidente: int,
    usuario: Usuario,
    payload: UbicacionTecnicoIn,
) -> UbicacionTecnicoOut:
    incidente = await _incidente_asignado_al_taller(db, id_incidente, usuario)
    location = atencion_realtime_manager.set_location(
        id_incidente,
        {
            "id_incidente": id_incidente,
            "id_usuario": usuario.id_usuario,
            "lat": payload.lat,
            "lng": payload.lng,
            "precision": payload.precision,
            "velocidad": payload.velocidad,
            "rumbo": payload.rumbo,
        },
    )
    out = _ubicacion_out(location)
    assert out is not None
    await atencion_realtime_manager.broadcast(
        id_incidente,
        {
            "tipo": "UBICACION_TECNICO",
            "id_incidente": incidente.id_incidente,
            "data": out.model_dump(mode="json"),
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    return out


async def aceptar_atencion(
    db: AsyncSession,
    id_incidente: int,
    usuario: Usuario,
    observacion: str | None,
) -> AtencionEventoOut:
    incidente = await _incidente_asignado_al_taller(db, id_incidente, usuario)
    estado_anterior = incidente.estado
    incidente.estado = "EN_PROCESO"

    obs = observacion or "Atencion aceptada por el taller asignado"
    await _registrar_historial(db, incidente, estado_anterior, incidente.estado, obs)
    await _registrar_bitacora(db, usuario, "Acepto atencion", incidente)
    await db.commit()
    await db.refresh(incidente)

    evento = _evento("ATENCION_ACEPTADA", incidente, obs)
    await _notificar_y_emitir(db, incidente, evento, "Atencion aceptada", obs)
    return evento


async def rechazar_atencion(
    db: AsyncSession,
    id_incidente: int,
    usuario: Usuario,
    observacion: str | None,
) -> AtencionEventoOut:
    incidente = await _incidente_asignado_al_taller(db, id_incidente, usuario)
    estado_anterior = incidente.estado
    taller_anterior = incidente.id_taller
    destinatarios = await _destinatarios(db, incidente)
    incidente.id_taller = None
    incidente.estado = "REPORTADO"

    obs = observacion or "Atencion rechazada por el taller asignado"
    await _registrar_historial(
        db,
        incidente,
        estado_anterior,
        incidente.estado,
        f"{obs}. Taller anterior: {taller_anterior}",
    )
    await _registrar_bitacora(db, usuario, "Rechazo atencion", incidente)
    await db.commit()
    await db.refresh(incidente)

    evento = _evento("ATENCION_RECHAZADA", incidente, obs)
    await _notificar_y_emitir(db, incidente, evento, "Atencion rechazada", obs, destinatarios)
    return evento


async def actualizar_estado_atencion(
    db: AsyncSession,
    id_incidente: int,
    usuario: Usuario,
    estado: str,
    observacion: str | None,
) -> AtencionEventoOut:
    estado_normalizado = estado.strip().upper()
    if estado_normalizado not in ESTADOS_PERMITIDOS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Estado no permitido. Usa uno de: {', '.join(sorted(ESTADOS_PERMITIDOS))}",
        )

    incidente = await _incidente_asignado_al_taller(db, id_incidente, usuario)
    estado_anterior = incidente.estado
    if estado_anterior == estado_normalizado:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El incidente ya tiene ese estado")

    incidente.estado = estado_normalizado
    obs = observacion or f"Estado actualizado a {estado_normalizado}"
    await _registrar_historial(db, incidente, estado_anterior, estado_normalizado, obs)
    await _registrar_bitacora(db, usuario, f"Actualizo atencion a {estado_normalizado}", incidente)
    await db.commit()
    await db.refresh(incidente)

    evento = _evento("ESTADO_ATENCION_ACTUALIZADO", incidente, obs)
    await _notificar_y_emitir(db, incidente, evento, f"Incidente #{id_incidente} - {estado_normalizado}", obs)
    return evento


async def _incidente_asignado_al_taller(db: AsyncSession, id_incidente: int, usuario: Usuario) -> Incidente:
    if "TALLER" not in _roles(usuario):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo el taller puede modificar la atencion")
    return await obtener_incidente_accesible(db, id_incidente, usuario)


async def _historial(db: AsyncSession, incidente: Incidente) -> list[IncidenteHistorialOut]:
    result = await db.execute(
        select(IncidenteHistorial)
        .where(
            IncidenteHistorial.id_incidente == incidente.id_incidente,
            IncidenteHistorial.id_tenant == incidente.id_tenant,
        )
        .order_by(IncidenteHistorial.created_at.desc())
    )
    return [IncidenteHistorialOut.model_validate(item) for item in result.scalars().all()]


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


async def _registrar_bitacora(db: AsyncSession, usuario: Usuario, accion: str, incidente: Incidente) -> None:
    rol = next(iter(_roles(usuario)), "DESCONOCIDO")
    db.add(
        Bitacora(
            id_tenant=usuario.id_tenant,
            modulo="CU18 Atencion en tiempo real",
            accion=f"{accion} para incidente #{incidente.id_incidente}",
            rol=rol,
            usuario_email=usuario.email,
            id_usuario=usuario.id_usuario,
        )
    )


async def _notificar_y_emitir(
    db: AsyncSession,
    incidente: Incidente,
    evento: AtencionEventoOut,
    titulo: str,
    mensaje: str,
    destinatarios: list[int] | None = None,
) -> None:
    destinatarios = destinatarios or await _destinatarios(db, incidente)
    for id_usuario in destinatarios:
        try:
            await notificacion_service.crear_notificacion(
                db=db,
                id_usuario=id_usuario,
                titulo=titulo,
                mensaje=mensaje,
                tipo=evento.tipo,
                id_incidente=incidente.id_incidente,
                id_tenant=incidente.id_tenant,
            )
        except Exception:
            pass

    await atencion_realtime_manager.broadcast(incidente.id_incidente, evento.model_dump(mode="json"))


async def _destinatarios(db: AsyncSession, incidente: Incidente) -> list[int]:
    destinatarios: list[int] = []
    cliente_r = await db.execute(
        select(Cliente).where(
            Cliente.id_cliente == incidente.id_cliente,
            Cliente.id_tenant == incidente.id_tenant,
        )
    )
    cliente = cliente_r.scalar_one_or_none()
    if cliente:
        destinatarios.append(cliente.id_usuario)

    if incidente.id_taller:
        taller_r = await db.execute(
            select(Taller).where(
                Taller.id_taller == incidente.id_taller,
                Taller.id_tenant == incidente.id_tenant,
            )
        )
        taller = taller_r.scalar_one_or_none()
        if taller:
            destinatarios.append(taller.id_usuario)
    return list(dict.fromkeys(destinatarios))


def _incidente_out(incidente: Incidente) -> IncidenteOut:
    data = IncidenteOut.model_validate(incidente)
    if incidente.taller:
        data.taller_nombre = incidente.taller.razon_social
    if incidente.vehiculo:
        data.vehiculo_placa = incidente.vehiculo.placa
        data.vehiculo_marca = incidente.vehiculo.marca
        data.vehiculo_modelo = incidente.vehiculo.modelo
    return data


def _evento(tipo: str, incidente: Incidente, observacion: str | None) -> AtencionEventoOut:
    return AtencionEventoOut(
        tipo=tipo,
        id_incidente=incidente.id_incidente,
        estado=incidente.estado,
        observacion=observacion,
        created_at=datetime.now(timezone.utc),
    )


def _ubicacion_out(data: dict | None) -> UbicacionTecnicoOut | None:
    if not data:
        return None
    normalized = dict(data)
    updated_at = normalized.get("updated_at")
    if isinstance(updated_at, str):
        normalized["updated_at"] = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
    return UbicacionTecnicoOut(**normalized)
