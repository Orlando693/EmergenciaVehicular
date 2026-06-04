from fastapi import APIRouter, Depends

from app.core.dependencies import CurrentUser, DBDep, require_roles
from app.gestion_operativa_atencion.cotizaciones.schemas import (
    CotizacionReparacionOut,
    CotizacionRespuestaUpdate,
    CotizacionSolicitudCreate,
)
from app.gestion_operativa_atencion.cotizaciones import service as cotizacion_service

router = APIRouter(
    prefix="/cotizaciones",
    tags=["CU20 - Cotizaciones de Reparación"],
)


@router.post(
    "/solicitar",
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
    "",
    response_model=list[CotizacionReparacionOut],
    summary="CU20 - Listar cotizaciones de reparacion",
    dependencies=[Depends(require_roles("CLIENTE", "TALLER"))],
)
async def listar_cotizaciones(db: DBDep, current_user: CurrentUser):
    return await cotizacion_service.listar_cotizaciones(db, current_user)


@router.get(
    "/{id_cotizacion}",
    response_model=CotizacionReparacionOut,
    summary="CU20 - Consultar cotizacion de reparacion",
    dependencies=[Depends(require_roles("CLIENTE", "TALLER"))],
)
async def obtener_cotizacion(id_cotizacion: int, db: DBDep, current_user: CurrentUser):
    return await cotizacion_service.obtener_cotizacion(db, current_user, id_cotizacion)


@router.patch(
    "/{id_cotizacion}/responder",
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
