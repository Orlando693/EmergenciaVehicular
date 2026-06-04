from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CotizacionComparacionOut(BaseModel):
    """Cotización enriquecida con datos del taller para comparación (paso 4 del flujo)."""

    id_cotizacion: int
    id_incidente: int
    id_taller: int

    # Datos del taller
    taller_nombre: str | None = None
    taller_direccion: str | None = None
    taller_calificacion: Decimal | None = None
    taller_acepta_remolque: bool = False

    # Detalles de la cotización
    descripcion_solicitud: str | None = None
    precio_estimado: Decimal | None = None
    detalle_danio: str | None = None
    condiciones_servicio: str | None = None
    tiempo_estimado: str | None = None

    estado: str
    respuesta_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SeleccionTallerRequest(BaseModel):
    """Payload para que el cliente seleccione una cotización (paso 6 del flujo)."""

    id_cotizacion: int = Field(..., description="ID de la cotización aceptada")


class SeleccionTallerOut(BaseModel):
    """Resultado de la selección de taller."""

    id_incidente: int
    id_taller: int
    id_cotizacion_aceptada: int
    taller_nombre: str | None = None
    taller_direccion: str | None = None
    estado_incidente: str
    cotizaciones_rechazadas: int = Field(
        0, description="Número de otras cotizaciones rechazadas automáticamente"
    )
    mensaje: str
