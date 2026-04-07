from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    rol: str
    id_usuario: int
    nombre: str


class TokenData(BaseModel):
    id_usuario: int | None = None
    email: str | None = None
    roles: list[str] = []
