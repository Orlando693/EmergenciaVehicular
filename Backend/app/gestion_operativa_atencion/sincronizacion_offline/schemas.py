from datetime import datetime

from pydantic import BaseModel, Field

from app.gestion_incidentes.incidentes.schemas import IncidenteCreate, IncidenteOut


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
