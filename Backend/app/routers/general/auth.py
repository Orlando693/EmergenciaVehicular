from fastapi import APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from fastapi import Depends

from app.core.dependencies import DBDep
from app.schemas.auth import LoginRequest, Token
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login", response_model=Token, summary="CU1 - Inicio de sesión")
async def login(form: LoginRequest, db: DBDep):
    """
    Autentica al usuario y devuelve un JWT.
    - **email**: correo del usuario
    - **password**: contraseña
    """
    return await auth_service.login(form.email, form.password, db)


@router.post("/login/form", response_model=Token, include_in_schema=False)
async def login_form(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DBDep):
    """Endpoint compatible con el formulario OAuth2 de Swagger UI."""
    return await auth_service.login(form.username, form.password, db)
