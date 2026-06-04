from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CotizacionSolicitudCreate(BaseModel):
    id_incidente: int
    descripcion_solicitud: str | None = Field(None, max_length=500)


class CotizacionRespuestaUpdate(BaseModel):
    precio_estimado: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2)
    detalle_danio: str = Field(..., min_length=5, max_length=1000)
    condiciones_servicio: str = Field(..., min_length=5, max_length=1000)
    tiempo_estimado: str = Field(..., min_length=2, max_length=100)


class CotizacionReparacionOut(BaseModel):
    id_cotizacion: int
    id_incidente: int
    id_cliente: int
    id_taller: int
    descripcion_solicitud: str | None = None
    estado: str
    precio_estimado: Decimal | None = None
    detalle_danio: str | None = None
    condiciones_servicio: str | None = None
    tiempo_estimado: str | None = None
    respuesta_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    taller_nombre: str | None = None
    incidente_estado: str | None = None

    model_config = {"from_attributes": True}
