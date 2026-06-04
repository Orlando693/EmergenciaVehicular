from datetime import datetime

from pydantic import BaseModel, Field


class TenantCreate(BaseModel):
    nombre: str = Field(..., max_length=150)
    slug: str = Field(..., max_length=100)
    estado: str = Field("ACTIVO", max_length=30)


class TenantUpdate(BaseModel):
    nombre: str | None = Field(None, max_length=150)
    slug: str | None = Field(None, max_length=100)
    estado: str | None = Field(None, max_length=30)


class TenantOut(BaseModel):
    id_tenant: int
    nombre: str
    slug: str
    estado: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
