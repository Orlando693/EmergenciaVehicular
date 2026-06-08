from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.gestion_incidentes.incidentes.schemas import IncidenteHistorialOut, IncidenteOut


class AtencionAccionRequest(BaseModel):
    observacion: str | None = Field(None, max_length=500)


class AtencionEstadoUpdate(BaseModel):
    estado: str = Field(..., max_length=50)
    observacion: str | None = Field(None, max_length=500)


class UbicacionTecnicoIn(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    precision: float | None = Field(None, ge=0)
    velocidad: float | None = Field(None, ge=0)
    rumbo: float | None = Field(None, ge=0, le=360)


class UbicacionTecnicoOut(BaseModel):
    id_incidente: int
    id_usuario: int
    lat: float
    lng: float
    precision: float | None = None
    velocidad: float | None = None
    rumbo: float | None = None
    updated_at: datetime


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
    ubicacion_tecnico: UbicacionTecnicoOut | None = None
    historial: list[IncidenteHistorialOut] = Field(default_factory=list)
    participantes_en_linea: int = 0


class AtencionEventoOut(BaseModel):
    tipo: str
    id_incidente: int
    estado: str
    observacion: str | None = None
    created_at: datetime
