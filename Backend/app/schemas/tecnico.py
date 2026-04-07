from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel

from app.models.enums import EstadoTecnicoEnum


class TecnicoCreate(BaseModel):
    nombres: str
    apellidos: str
    telefono: str | None = None
    especialidad: str | None = None
    latitud: Decimal | None = None
    longitud: Decimal | None = None


class TecnicoUpdate(BaseModel):
    nombres: str | None = None
    apellidos: str | None = None
    telefono: str | None = None
    especialidad: str | None = None
    latitud: Decimal | None = None
    longitud: Decimal | None = None
    estado: EstadoTecnicoEnum | None = None
    activo: bool | None = None


class TecnicoOut(BaseModel):
    id_tecnico: int
    id_taller: int
    nombres: str
    apellidos: str
    telefono: str | None
    especialidad: str | None
    latitud: Decimal | None
    longitud: Decimal | None
    estado: EstadoTecnicoEnum
    activo: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
