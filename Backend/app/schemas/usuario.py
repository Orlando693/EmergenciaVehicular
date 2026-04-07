from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator

from app.models.enums import EstadoUsuarioEnum


class UsuarioCreate(BaseModel):
    nombres: str
    apellidos: str
    email: EmailStr
    password: str
    telefono: str | None = None
    rol: str = "CLIENTE"  # CLIENTE | TALLER | ADMINISTRADOR

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres")
        return v


class UsuarioUpdate(BaseModel):
    nombres: str | None = None
    apellidos: str | None = None
    telefono: str | None = None


class UsuarioEstadoUpdate(BaseModel):
    estado: EstadoUsuarioEnum


class UsuarioOut(BaseModel):
    id_usuario: int
    nombres: str
    apellidos: str
    email: str
    telefono: str | None
    estado: EstadoUsuarioEnum
    ultimo_acceso: datetime | None
    created_at: datetime
    roles: list[str] = []

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_roles(cls, usuario) -> "UsuarioOut":
        data = {
            "id_usuario": usuario.id_usuario,
            "nombres": usuario.nombres,
            "apellidos": usuario.apellidos,
            "email": usuario.email,
            "telefono": usuario.telefono,
            "estado": usuario.estado,
            "ultimo_acceso": usuario.ultimo_acceso,
            "created_at": usuario.created_at,
            "roles": [r.nombre for r in usuario.roles],
        }
        return cls(**data)


class CambiarPasswordRequest(BaseModel):
    password_actual: str
    password_nuevo: str

    @field_validator("password_nuevo")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres")
        return v
