from fastapi import APIRouter, Depends, status

from app.core.dependencies import CurrentUser, DBDep, require_roles
from app.gestion_comercial_servicio.procesar_pago_pasarela.schemas import (
    ConfirmarWebhookRequest,
    InfoPagoOut,
    PagoGatewayTransaccionOut,
    ProcesarPagoRequest,
    ResultadoPagoOut,
)
from app.gestion_comercial_servicio.procesar_pago_pasarela import service

router = APIRouter(
    prefix="/procesar-pago",
    tags=["CU23 - Procesar pago mediante pasarela externa"],
)


@router.get(
    "/{id_incidente}",
    response_model=InfoPagoOut,
    summary="CU23 - Pasos 2-3: Consultar monto y estado del pago pendiente",
    dependencies=[Depends(require_roles("CLIENTE"))],
)
async def obtener_info_pago(
    id_incidente: int,
    db: DBDep,
    current_user: CurrentUser,
):
    """
    El cliente consulta el monto total, la comisión y el estado de pago
    actual del servicio antes de iniciar la transacción.
    Aplica el precio de la cotización aceptada si existe; de lo contrario
    calcula el monto según la clasificación IA del incidente.
    """
    return await service.obtener_info_pago(db, id_incidente, current_user)


@router.post(
    "/{id_incidente}/procesar",
    response_model=ResultadoPagoOut,
    status_code=status.HTTP_200_OK,
    summary="CU23 - Pasos 4-13: Procesar pago mediante pasarela externa",
    dependencies=[Depends(require_roles("CLIENTE"))],
)
async def procesar_pago(
    id_incidente: int,
    payload: ProcesarPagoRequest,
    db: DBDep,
    current_user: CurrentUser,
):
    """
    El cliente envía sus datos de pago. El sistema llama a la pasarela
    externa y retorna el resultado de la transacción.

    **Estados posibles del pago:**
    - `COMPLETADO` → transacción aprobada, incidente marcado como PAGADO.
    - `FALLIDO` → transacción rechazada; el cliente puede reintentar.
    - `PENDIENTE` → la pasarela no confirmó aún; se confirma vía webhook.

    **Sandbox — tarjetas de prueba:**
    | Últimos 4 dígitos | Resultado    |
    |-------------------|--------------|
    | `0000`            | RECHAZADO    |
    | `0001`            | PENDIENTE    |
    | Cualquier otro    | APROBADO     |
    """
    return await service.procesar_pago_gateway(db, id_incidente, payload, current_user)


@router.post(
    "/webhook/confirmar",
    response_model=ResultadoPagoOut,
    status_code=status.HTTP_200_OK,
    summary="CU23 - Paso 8-11: Webhook de confirmación de la pasarela",
)
async def confirmar_webhook(
    payload: ConfirmarWebhookRequest,
    db: DBDep,
):
    """
    Endpoint llamado directamente por la pasarela externa para confirmar
    o rechazar una transacción que quedó en estado PENDIENTE.
    No requiere autenticación de usuario (la valida la pasarela con su secreto).

    En producción agregar validación de firma/secreto del gateway (HMAC).
    """
    return await service.confirmar_webhook(db, payload)


@router.get(
    "/{id_incidente}/transacciones",
    response_model=list[PagoGatewayTransaccionOut],
    summary="CU23 - Historial de intentos de pago",
    dependencies=[Depends(require_roles("CLIENTE"))],
)
async def listar_transacciones(
    id_incidente: int,
    db: DBDep,
    current_user: CurrentUser,
):
    """
    Devuelve todos los intentos de pago registrados para el servicio,
    ordenados por número de intento ascendente.
    """
    return await service.listar_transacciones(db, id_incidente, current_user)
