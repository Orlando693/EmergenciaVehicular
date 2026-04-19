from datetime import datetime
from pydantic import BaseModel, Field

class IncidenteCreate(BaseModel):
    id_vehiculo: int
    descripcion: str = Field(..., max_length=1000)
    ubicacion_lat: float | None = None
    ubicacion_lng: float | None = None
    direccion: str | None = Field(None, max_length=255)
    # The urls would ideally come from a file upload processed by S3/Firebase/Cloudinary 
    # but here we receive strings (urls) for simplicity in the case
    audio_url: str | None = Field(None, max_length=255)
    imagen_url: str | None = Field(None, max_length=255)

class IncidenteOut(BaseModel):
    id_incidente: int
    id_cliente: int
    id_vehiculo: int | None
    id_taller: int | None
    descripcion: str
    audio_url: str | None = None
    imagen_url: str | None = None
    resumen_ia: str | None = None
    clasificacion_ia: str | None = None
    ubicacion_lat: float | None
    ubicacion_lng: float | None
    direccion: str | None
    estado: str
    created_at: datetime
    updated_at: datetime
    
    # Optional fields for relationships
    taller_nombre: str | None = None
    vehiculo_placa: str | None = None
    vehiculo_marca: str | None = None
    vehiculo_modelo: str | None = None

    model_config = {"from_attributes": True}

class IncidenteEstadoUpdate(BaseModel):
    estado: str
    observacion: str | None = Field(None, max_length=500)

class IncidenteHistorialOut(BaseModel):
    id_historial: int
    estado_anterior: str | None = None
    estado_nuevo: str
    observacion: str | None = None
    created_at: datetime
    
    model_config = {"from_attributes": True}