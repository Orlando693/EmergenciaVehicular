from fastapi import APIRouter, Depends, status

from app.core.dependencies import CurrentUser, DBDep, require_roles
from app.gestion_operativa_atencion.gestionar_atencion_reparacion.schemas import (
    EstimacionAtencionCreate,
    EstimacionAtencionOut,
    EstimacionAtencionUpdate,
)
from app.gestion_operativa_atencion.gestionar_atencion_reparacion import service

router = APIRouter(
    prefix="/gestionar-atencion",
    tags=["CU22 - Gestionar estimación de atención y reparación"],
)


@router.post(
    "/{id_incidente}/estimacion",
    response_model=EstimacionAtencionOut,
    status_code=status.HTTP_201_CREATED,
    summary="CU22 - Pasos 4-7: Registrar estimación de llegada y reparación",
    dependencies=[Depends(require_roles("TALLER"))],
)
async def registrar_estimacion(
    id_incidente: int,
    payload: EstimacionAtencionCreate,
    db: DBDep,
    current_user: CurrentUser,
):
    """
    El taller registra por primera vez los tiempos estimados de llegada
    y reparación para el incidente asignado.

    - El incidente debe estar asignado al taller autenticado.
    - Notifica automáticamente al cliente (paso 8).
    - Registra el evento en bitácora (paso 11).
    """
    return await service.registrar_estimacion(db, id_incidente, payload, current_user)


@router.patch(
    "/{id_incidente}/estimacion",
    response_model=EstimacionAtencionOut,
    summary="CU22 - Paso 9-11: Actualizar estimación durante la atención",
    dependencies=[Depends(require_roles("TALLER"))],
)
async def actualizar_estimacion(
    id_incidente: int,
    payload: EstimacionAtencionUpdate,
    db: DBDep,
    current_user: CurrentUser,
):
    """
    El taller actualiza las estimaciones cuando hay cambios durante la atención.

    - Solo es necesario enviar los campos que cambian.
    - Notifica automáticamente al cliente con la actualización (paso 10).
    - Registra el evento en bitácora (paso 11).
    """
    return await service.actualizar_estimacion(db, id_incidente, payload, current_user)


@router.get(
    "/{id_incidente}/estimacion",
    response_model=EstimacionAtencionOut,
    summary="CU22 - Consultar estimación vigente (TALLER o CLIENTE)",
    dependencies=[Depends(require_roles("TALLER", "CLIENTE"))],
)
async def obtener_estimacion(
    id_incidente: int,
    db: DBDep,
    current_user: CurrentUser,
):
    """
    Devuelve la estimación vigente del incidente.

    - El **TALLER** debe ser el asignado al incidente.
    - El **CLIENTE** debe ser el dueño del incidente.
    """
    return await service.obtener_estimacion(db, id_incidente, current_user)
