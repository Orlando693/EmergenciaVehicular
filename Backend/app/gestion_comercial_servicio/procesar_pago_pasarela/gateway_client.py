"""
Abstracción de la pasarela de pagos externa.

Patrón Adapter: todo el código de negocio de CU23 llama únicamente a
`procesar_pago()`. Para integrar Stripe, PayPal, Culqi, etc., se reemplaza
solo el contenido de `_llamar_gateway_externo()`; el resto del flujo no cambia.

Sandbox de prueba (tarjeta):
  - Últimos 4 dígitos "0000"   → RECHAZADO
  - Últimos 4 dígitos "0001"   → PENDIENTE (gateway necesita confirmación)
  - Cualquier otro número/vacío → APROBADO
TRANSFERENCIA / QR / EFECTIVO → siempre APROBADO.
"""

import asyncio
import random
import string
from dataclasses import dataclass, field
from decimal import Decimal


# ── DTO de respuesta ──────────────────────────────────────────────────────────

@dataclass
class GatewayRespuesta:
    estado: str          # APROBADO | RECHAZADO | PENDIENTE | ERROR_CONEXION
    referencia: str      # ID de la transacción en el gateway externo
    codigo: str          # Código de respuesta (ej. "00", "05", "TIMEOUT")
    mensaje: str         # Mensaje legible


# ── Códigos de estado normalizados ───────────────────────────────────────────

ESTADO_APROBADO         = "APROBADO"
ESTADO_RECHAZADO        = "RECHAZADO"
ESTADO_PENDIENTE        = "PENDIENTE"
ESTADO_ERROR_CONEXION   = "ERROR_CONEXION"


# ── Entrada del cliente ───────────────────────────────────────────────────────

@dataclass
class DatosPago:
    metodo_pago:    str              # TARJETA | TRANSFERENCIA | QR | EFECTIVO
    monto:          Decimal
    numero_tarjeta: str | None = None
    nombre_titular: str | None = None
    vencimiento:    str | None = None
    cvv:            str | None = None


# ── API pública ───────────────────────────────────────────────────────────────

async def procesar_pago(datos: DatosPago, gateway: str = "PASARELA_SANDBOX") -> GatewayRespuesta:
    """
    Punto de entrada único. Delega al adaptador del gateway indicado.
    En producción se añaden más adaptadores (STRIPE, PAYPAL, CULQI…).
    """
    if gateway == "PASARELA_SANDBOX":
        return await _sandbox(datos)
    # TODO: añadir adaptadores reales
    # elif gateway == "STRIPE":
    #     return await _stripe(datos)
    raise ValueError(f"Gateway '{gateway}' no soportado")


# ── Sandbox (simulación) ──────────────────────────────────────────────────────

async def _sandbox(datos: DatosPago) -> GatewayRespuesta:
    """
    Simula una llamada HTTP asíncrona a la pasarela.
    Latencia artificial de 150 ms para replicar comportamiento real.
    """
    await asyncio.sleep(0.15)

    referencia = _generar_referencia()
    metodo = (datos.metodo_pago or "").upper()

    if metodo in ("TRANSFERENCIA", "QR", "EFECTIVO"):
        return GatewayRespuesta(
            estado=ESTADO_APROBADO,
            referencia=referencia,
            codigo="00",
            mensaje="Transacción aprobada",
        )

    ultimos = (datos.numero_tarjeta or "").replace(" ", "")[-4:]

    if ultimos == "0000":
        return GatewayRespuesta(
            estado=ESTADO_RECHAZADO,
            referencia=referencia,
            codigo="05",
            mensaje="Tarjeta declinada. Verifique los datos o intente con otra tarjeta.",
        )

    if ultimos == "0001":
        return GatewayRespuesta(
            estado=ESTADO_PENDIENTE,
            referencia=referencia,
            codigo="68",
            mensaje="Transacción pendiente de confirmación por el banco emisor.",
        )

    return GatewayRespuesta(
        estado=ESTADO_APROBADO,
        referencia=referencia,
        codigo="00",
        mensaje="Transacción aprobada",
    )


# ── Helper ────────────────────────────────────────────────────────────────────

def _generar_referencia() -> str:
    chars = string.ascii_uppercase + string.digits
    return "GW-" + "".join(random.choices(chars, k=12))
