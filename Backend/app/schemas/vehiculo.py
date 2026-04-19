from datetime import datetime
from pydantic import BaseModel, Field

class VehiculoBase(BaseModel):
    placa: str = Field(..., max_length=20)
    marca: str = Field(..., max_length=80)
    modelo: str = Field(..., max_length=80)
    anio: int | None = None
    color: str | None = Field(None, max_length=50)
    tipo_vehiculo: str | None = Field(None, max_length=50)
    vin: str | None = Field(None, max_length=50)

class VehiculoCreate(VehiculoBase):
    pass

class VehiculoUpdate(BaseModel):
    placa: str | None = Field(None, max_length=20)
    marca: str | None = Field(None, max_length=80)
    modelo: str | None = Field(None, max_length=80)
    anio: int | None = None
    color: str | None = Field(None, max_length=50)
    tipo_vehiculo: str | None = Field(None, max_length=50)
    vin: str | None = Field(None, max_length=50)
    activo: bool | None = None

class VehiculoOut(VehiculoBase):
    id_vehiculo: int
    id_cliente: int
    activo: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
