from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, EmailStr, field_validator

from app.models.enums import EstadoTallerEnum


class TallerCreate(BaseModel):
    razon_social: str
    nombre_comercial: str
    nit: str | None = None
    telefono_atencion: str | None = None
    email_atencion: EmailStr | None = None
    direccion: str
    referencia: str | None = None
    latitud: Decimal | None = None
    longitud: Decimal | None = None
    capacidad_maxima: int = 1
    acepta_remolque: bool = False

    @field_validator("capacidad_maxima")
    @classmethod
    def capacidad_positiva(cls, v: int) -> int:
        if v < 1:
            raise ValueError("La capacidad máxima debe ser mayor a 0")
        return v


class TallerUpdate(BaseModel):
    razon_social: str | None = None
    nombre_comercial: str | None = None
    nit: str | None = None
    telefono_atencion: str | None = None
    email_atencion: EmailStr | None = None
    direccion: str | None = None
    referencia: str | None = None
    latitud: Decimal | None = None
    longitud: Decimal | None = None
    capacidad_maxima: int | None = None
    acepta_remolque: bool | None = None


class TallerEstadoUpdate(BaseModel):
    estado_registro: EstadoTallerEnum
    observacion: str | None = None


class TallerOut(BaseModel):
    id_taller: int
    id_usuario: int
    razon_social: str
    nombre_comercial: str
    nit: str | None
    telefono_atencion: str | None
    email_atencion: str | None
    direccion: str
    referencia: str | None
    latitud: Decimal | None
    longitud: Decimal | None
    capacidad_maxima: int
    acepta_remolque: bool
    estado_registro: EstadoTallerEnum
    calificacion_promedio: Decimal | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
