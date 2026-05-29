from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.incidente import IncidenteCreate, IncidenteHistorialOut, IncidenteOut


class AtencionAccionRequest(BaseModel):
    observacion: str | None = Field(None, max_length=500)


class AtencionEstadoUpdate(BaseModel):
    estado: str = Field(..., max_length=50)
    observacion: str | None = Field(None, max_length=500)


class TallerSeguimientoOut(BaseModel):
    id_taller: int
    razon_social: str
    nombre_comercial: str
    telefono_atencion: str | None = None
    latitud: Decimal | None = None
    longitud: Decimal | None = None

    model_config = {"from_attributes": True}


class AtencionSeguimientoOut(BaseModel):
    incidente: IncidenteOut
    taller: TallerSeguimientoOut | None = None
    historial: list[IncidenteHistorialOut] = Field(default_factory=list)
    participantes_en_linea: int = 0


class AtencionEventoOut(BaseModel):
    tipo: str
    id_incidente: int
    estado: str
    observacion: str | None = None
    created_at: datetime


class EmergenciaOfflineSyncRequest(BaseModel):
    client_sync_id: str = Field(..., min_length=8, max_length=100)
    emergencia: IncidenteCreate
    created_at_local: datetime | None = None


class EmergenciaOfflineSyncOut(BaseModel):
    client_sync_id: str
    estado_sync: str
    id_incidente: int | None = None
    incidente: IncidenteOut | None = None
    mensaje: str
    error_mensaje: str | None = None
    intentos: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None


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
