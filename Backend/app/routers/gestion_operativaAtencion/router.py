from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.dependencies import CurrentUser, DBDep, require_roles
from app.core.security import decode_token
from app.database import AsyncSessionLocal
from app.models.usuario import Usuario
from app.schemas.atencion_tiempo_real import (
    AtencionAccionRequest,
    AtencionEstadoUpdate,
    AtencionEventoOut,
    AtencionSeguimientoOut,
    CotizacionReparacionOut,
    CotizacionRespuestaUpdate,
    CotizacionSolicitudCreate,
    EmergenciaOfflineSyncOut,
    EmergenciaOfflineSyncRequest,
)
from app.services.gestion_operativaAtencion import cotizacion_service, offline_sync_service, service
from app.services.gestion_operativaAtencion.manager import atencion_realtime_manager

router = APIRouter(
    prefix="/atencion-tiempo-real",
    tags=["CU18 - Atencion en tiempo real"],
)


@router.post(
    "/cotizaciones/solicitar",
    response_model=CotizacionReparacionOut,
    summary="CU20 - Solicitar cotizacion de reparacion",
    dependencies=[Depends(require_roles("CLIENTE"))],
)
async def solicitar_cotizacion(
    payload: CotizacionSolicitudCreate,
    db: DBDep,
    current_user: CurrentUser,
):
    return await cotizacion_service.solicitar_cotizacion(db, current_user, payload)


@router.get(
    "/cotizaciones",
    response_model=list[CotizacionReparacionOut],
    summary="CU20 - Listar cotizaciones de reparacion",
    dependencies=[Depends(require_roles("CLIENTE", "TALLER"))],
)
async def listar_cotizaciones(db: DBDep, current_user: CurrentUser):
    return await cotizacion_service.listar_cotizaciones(db, current_user)


@router.get(
    "/cotizaciones/{id_cotizacion}",
    response_model=CotizacionReparacionOut,
    summary="CU20 - Consultar cotizacion de reparacion",
    dependencies=[Depends(require_roles("CLIENTE", "TALLER"))],
)
async def obtener_cotizacion(id_cotizacion: int, db: DBDep, current_user: CurrentUser):
    return await cotizacion_service.obtener_cotizacion(db, current_user, id_cotizacion)


@router.patch(
    "/cotizaciones/{id_cotizacion}/responder",
    response_model=CotizacionReparacionOut,
    summary="CU20 - Responder cotizacion de reparacion",
    dependencies=[Depends(require_roles("TALLER"))],
)
async def responder_cotizacion(
    id_cotizacion: int,
    payload: CotizacionRespuestaUpdate,
    db: DBDep,
    current_user: CurrentUser,
):
    return await cotizacion_service.responder_cotizacion(db, current_user, id_cotizacion, payload)


@router.post(
    "/sincronizar-emergencia-offline",
    response_model=EmergenciaOfflineSyncOut,
    summary="CU19 - Sincronizar emergencia registrada sin conexion",
    dependencies=[Depends(require_roles("CLIENTE"))],
)
async def sincronizar_emergencia_offline(
    payload: EmergenciaOfflineSyncRequest,
    db: DBDep,
    current_user: CurrentUser,
):
    return await offline_sync_service.sincronizar_emergencia_offline(db, current_user, payload)


@router.get(
    "/sincronizaciones/{client_sync_id}",
    response_model=EmergenciaOfflineSyncOut,
    summary="CU19 - Consultar estado de sincronizacion offline",
    dependencies=[Depends(require_roles("CLIENTE"))],
)
async def obtener_estado_sincronizacion(
    client_sync_id: str,
    db: DBDep,
    current_user: CurrentUser,
):
    return await offline_sync_service.obtener_estado_sincronizacion(db, current_user, client_sync_id)


@router.get(
    "/{id_incidente}",
    response_model=AtencionSeguimientoOut,
    dependencies=[Depends(require_roles("CLIENTE", "TALLER"))],
)
async def obtener_seguimiento(id_incidente: int, db: DBDep, current_user: CurrentUser):
    return await service.obtener_seguimiento(db, id_incidente, current_user)


@router.post(
    "/{id_incidente}/aceptar",
    response_model=AtencionEventoOut,
    dependencies=[Depends(require_roles("TALLER"))],
)
async def aceptar_atencion(
    id_incidente: int,
    payload: AtencionAccionRequest,
    db: DBDep,
    current_user: CurrentUser,
):
    return await service.aceptar_atencion(db, id_incidente, current_user, payload.observacion)


@router.post(
    "/{id_incidente}/rechazar",
    response_model=AtencionEventoOut,
    dependencies=[Depends(require_roles("TALLER"))],
)
async def rechazar_atencion(
    id_incidente: int,
    payload: AtencionAccionRequest,
    db: DBDep,
    current_user: CurrentUser,
):
    return await service.rechazar_atencion(db, id_incidente, current_user, payload.observacion)


@router.patch(
    "/{id_incidente}/estado",
    response_model=AtencionEventoOut,
    dependencies=[Depends(require_roles("TALLER"))],
)
async def actualizar_estado_atencion(
    id_incidente: int,
    payload: AtencionEstadoUpdate,
    db: DBDep,
    current_user: CurrentUser,
):
    return await service.actualizar_estado_atencion(
        db,
        id_incidente,
        current_user,
        payload.estado,
        payload.observacion,
    )


@router.websocket("/{id_incidente}/ws")
async def ws_atencion(id_incidente: int, ws: WebSocket, token: str = Query(...)):
    try:
        token_data = decode_token(token)
    except Exception:
        await ws.close(code=1008)
        return

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Usuario)
            .where(Usuario.id_usuario == token_data.id_usuario)
            .options(selectinload(Usuario.roles))
        )
        usuario = result.scalar_one_or_none()
        if (
            not usuario
            or usuario.id_tenant is None
            or token_data.id_tenant is None
            or int(usuario.id_tenant) != int(token_data.id_tenant)
        ):
            await ws.close(code=1008)
            return

        try:
            seguimiento = await service.obtener_seguimiento(db, id_incidente, usuario)
        except Exception:
            await ws.close(code=1008)
            return

    await atencion_realtime_manager.join(ws, id_incidente, token_data.id_usuario)
    await ws.send_json({
        "tipo": "SEGUIMIENTO_INICIAL",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "data": seguimiento.model_dump(mode="json"),
    })

    try:
        while True:
            data = await ws.receive_json()
            if data.get("tipo") == "ping":
                await ws.send_json({"tipo": "pong", "created_at": datetime.now(timezone.utc).isoformat()})
    except WebSocketDisconnect:
        atencion_realtime_manager.leave(id_incidente, token_data.id_usuario)
