from datetime import datetime
from pydantic import BaseModel


class RolCreate(BaseModel):
    nombre: str
    descripcion: str | None = None


class RolUpdate(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None
    activo: bool | None = None


class PermisoOut(BaseModel):
    id_permiso: int
    codigo: str
    descripcion: str | None

    model_config = {"from_attributes": True}


class RolOut(BaseModel):
    id_rol: int
    nombre: str
    descripcion: str | None
    activo: bool
    created_at: datetime
    permisos: list[PermisoOut] = []

    model_config = {"from_attributes": True}


class AsignarPermisoRequest(BaseModel):
    id_permisos: list[int]


class AsignarRolRequest(BaseModel):
    id_roles: list[int]


class PermisoCreate(BaseModel):
    codigo: str
    descripcion: str | None = None
