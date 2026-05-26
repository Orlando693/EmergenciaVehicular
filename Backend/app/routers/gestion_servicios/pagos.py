from fastapi import APIRouter, Depends

from app.core.dependencies import DBDep, CurrentUser, require_roles
from app.schemas.pago import CostoEstimado, IniciarPagoRequest, PagoOut, PagoPage, InfoPago
from app.services import pago_service

router = APIRouter(prefix="/pagos", tags=["Pagos", "CU16"])


@router.get("/mis-pagos", response_model=PagoPage)
async def mis_pagos(
    db: DBDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 20,
    _=Depends(require_roles("CLIENTE")),
):
    """Lista todos los pagos realizados por el cliente autenticado."""
    return await pago_service.listar_pagos_cliente(current_user.id_usuario, db, skip=skip, limit=limit)


@router.get("/admin/todos", response_model=PagoPage)
async def todos_pagos(
    db: DBDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 50,
    _=Depends(require_roles("ADMINISTRADOR")),
):
    """Lista todos los pagos (solo administradores)."""
    return await pago_service.listar_todos_pagos(db, skip=skip, limit=limit)


@router.get("/incidente/{id_incidente}/costo", response_model=CostoEstimado)
async def obtener_costo(
    id_incidente: int,
    db: DBDep,
    current_user: CurrentUser,
    _=Depends(require_roles("CLIENTE")),
):
    """Calcula el costo estimado del servicio y devuelve el pago existente si lo hay."""
    return await pago_service.obtener_costo(id_incidente, current_user.id_usuario, db)


@router.get(
    "/incidente/{id_incidente}/info",
    response_model=InfoPago,
    summary="A2 - Info de pago para CLIENTE dueño, TALLER asignado o ADMIN",
)
async def obtener_info_pago_endpoint(
    id_incidente: int,
    db: DBDep,
    current_user: CurrentUser,
    _=Depends(require_roles("CLIENTE", "TALLER", "ADMINISTRADOR")),
):
    """Devuelve el costo y el pago existente del incidente.
    - CLIENTE: solo si es dueño del incidente.
    - TALLER:  solo si el incidente está asignado a su taller.
    - ADMIN:   siempre.
    A diferencia de /costo, no exige estado RESUELTO; sirve para mostrar el pago aunque ya esté PAGADO."""
    nombres = {r.nombre.upper() for r in current_user.roles}
    return await pago_service.obtener_info_pago(
        id_incidente=id_incidente,
        id_usuario=current_user.id_usuario,
        es_admin=("ADMINISTRADOR" in nombres),
        es_taller=("TALLER" in nombres),
        es_cliente=("CLIENTE" in nombres),
        db=db,
    )


@router.post("/incidente/{id_incidente}/pagar", response_model=PagoOut)
async def realizar_pago(
    id_incidente: int,
    body: IniciarPagoRequest,
    db: DBDep,
    current_user: CurrentUser,
    _=Depends(require_roles("CLIENTE")),
):
    """Procesa el pago del servicio finalizado."""
    return await pago_service.iniciar_pago(
        id_incidente=id_incidente,
        id_usuario=current_user.id_usuario,
        metodo_pago=body.metodo_pago,
        numero_tarjeta=body.numero_tarjeta,
        db=db,
    )
