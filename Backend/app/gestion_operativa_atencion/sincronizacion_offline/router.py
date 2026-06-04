from fastapi import APIRouter, Depends

from app.core.dependencies import CurrentUser, DBDep, require_roles
from app.gestion_operativa_atencion.sincronizacion_offline.schemas import (
    EmergenciaOfflineSyncOut,
    EmergenciaOfflineSyncRequest,
)
from app.gestion_operativa_atencion.sincronizacion_offline import service as offline_sync_service

router = APIRouter(
    prefix="/sincronizacion-offline",
    tags=["CU19 - Sincronización Offline"],
)


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
