from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    tenant_slug: str | None = None  # requerido solo si el email existe en más de un tenant


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    rol: str
    id_usuario: int
    nombre: str
    id_tenant: int
    tenant_nombre: str | None = None
    tenant_slug: str | None = None


class TokenData(BaseModel):
    id_usuario: int | None = None
    email: str | None = None
    roles: list[str] = []
    id_tenant: int | None = None
