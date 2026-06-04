from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.gestion_incidentes.incidentes.schemas import IncidenteHistorialOut, IncidenteOut


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
