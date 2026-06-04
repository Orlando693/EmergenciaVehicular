from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import CurrentUser, DBDep, require_roles
from app.gestion_comercial_servicio.seleccionar_taller_servicio.schemas import (
    CotizacionComparacionOut,
    SeleccionTallerOut,
    SeleccionTallerRequest,
)
from app.gestion_comercial_servicio.seleccionar_taller_servicio import service

router = APIRouter(
    prefix="/seleccionar-taller",
    tags=["CU21 - Seleccionar taller para el servicio"],
    dependencies=[Depends(require_roles("CLIENTE"))],
)


@router.get(
    "/{id_incidente}/cotizaciones",
    response_model=list[CotizacionComparacionOut],
    summary="CU21 - Paso 3-5: Listar y comparar cotizaciones disponibles",
)
async def listar_cotizaciones_para_seleccion(
    id_incidente: int,
    db: DBDep,
    current_user: CurrentUser,
):
    """
    Devuelve todas las cotizaciones en estado RESPONDIDA para la emergencia
    indicada, enriquecidas con los datos del taller (precio, tiempo estimado,
    condiciones y calificación) para que el cliente pueda compararlas.
    """
    return await service.listar_cotizaciones_para_seleccion(db, id_incidente, current_user)


@router.post(
    "/{id_incidente}/seleccionar",
    response_model=SeleccionTallerOut,
    status_code=status.HTTP_200_OK,
    summary="CU21 - Paso 6-11: Seleccionar el taller para el servicio",
)
async def seleccionar_taller(
    id_incidente: int,
    payload: SeleccionTallerRequest,
    db: DBDep,
    current_user: CurrentUser,
):
    """
    El cliente elige la cotización que más le convenga.

    - Valida que la cotización siga en estado RESPONDIDA.
    - Valida que el taller siga APROBADO.
    - Acepta la cotización seleccionada y rechaza automáticamente las demás.
    - Asigna el taller al incidente y lo pasa a estado EN_PROCESO.
    - Notifica al taller por WebSocket y push notification.
    - Registra el evento en bitácora.
    """
    return await service.seleccionar_taller(
        db, id_incidente, payload.id_cotizacion, current_user
    )


@router.get(
    "/{id_incidente}/seleccion",
    response_model=SeleccionTallerOut | None,
    summary="CU21 - Consultar el taller ya seleccionado",
)
async def obtener_seleccion_actual(
    id_incidente: int,
    db: DBDep,
    current_user: CurrentUser,
):
    """
    Devuelve la selección vigente para el incidente (cotización ACEPTADA),
    o null si el cliente aún no ha seleccionado taller.
    """
    return await service.obtener_seleccion_actual(db, id_incidente, current_user)
