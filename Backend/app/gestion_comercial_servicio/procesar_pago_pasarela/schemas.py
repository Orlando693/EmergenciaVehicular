from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


# ── Entrada del cliente ───────────────────────────────────────────────────────

class ProcesarPagoRequest(BaseModel):
    """
    Pasos 5-6 del flujo: datos del cliente para procesar el pago.
    Los datos de tarjeta solo se usan si metodo_pago == 'TARJETA'.
    Nunca se persisten; solo se pasan al gateway.
    """

    metodo_pago: str = Field(
        ...,
        examples=["TARJETA", "TRANSFERENCIA", "EFECTIVO"],
        description="Método de pago seleccionado",
    )
    numero_tarjeta: str | None = Field(
        None,
        max_length=19,
        description="Número de tarjeta (solo para TARJETA). Sandbox: '0000'=rechazo, '0001'=pendiente.",
    )
    nombre_titular: str | None = Field(None, max_length=150)
    vencimiento: str | None = Field(
        None, max_length=7, examples=["12/27"], description="MM/YY"
    )
    cvv: str | None = Field(None, max_length=4)

    gateway: str = Field(
        default="PASARELA_SANDBOX",
        description="Identificador de la pasarela. Valores disponibles: PASARELA_SANDBOX.",
    )


class ConfirmarWebhookRequest(BaseModel):
    """
    Payload del webhook enviado por la pasarela para confirmar una
    transacción que quedó en estado PENDIENTE.
    """

    gateway_referencia: str = Field(..., description="ID de la transacción en la pasarela")
    estado: str = Field(
        ...,
        examples=["APROBADO", "RECHAZADO"],
        description="Estado final reportado por la pasarela",
    )
    codigo: str | None = None
    mensaje: str | None = None


# ── Salidas ───────────────────────────────────────────────────────────────────

class InfoPagoOut(BaseModel):
    """Pasos 2-3: información del pago pendiente antes de procesar."""

    id_incidente: int
    estado_incidente: str
    monto_total: Decimal
    monto_taller: Decimal
    comision_plataforma: Decimal
    cotizacion_aceptada_id: int | None = None
    precio_cotizacion: Decimal | None = None
    pago_estado: str | None = Field(None, description="Estado del pago si ya existe")
    pago_referencia: str | None = None

    model_config = {"from_attributes": True}


class PagoGatewayTransaccionOut(BaseModel):
    """Resultado de un intento de pago contra la pasarela."""

    id_transaccion: int
    id_pago: int
    gateway_nombre: str
    metodo_pago: str
    monto: Decimal
    intento_numero: int
    gateway_referencia: str | None = None
    gateway_codigo: str | None = None
    gateway_mensaje: str | None = None
    estado: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ResultadoPagoOut(BaseModel):
    """Respuesta completa del proceso de pago (pasos 9-12)."""

    id_pago: int
    id_incidente: int
    estado_pago: str
    referencia: str | None = None
    monto_total: Decimal
    estado_incidente: str
    transaccion: PagoGatewayTransaccionOut
    mensaje: str
