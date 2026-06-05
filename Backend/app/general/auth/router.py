from fastapi import APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy import func, select

from app.core.dependencies import DBDep
from app.general.auth.schemas import LoginRequest, Token
from app.general.auth import service as auth_service
from app.administracion.tenants.model import Tenant

router = APIRouter(prefix="/auth", tags=["Autenticación"])


class WorkspaceInfo(BaseModel):
    nombre: str
    slug: str


@router.get(
    "/workspace/{slug}",
    response_model=WorkspaceInfo,
    summary="Verificar workspace por slug (público)",
)
async def verificar_workspace(slug: str, db: DBDep):
    """Endpoint público: verifica que el slug de tenant existe."""
    res = await db.execute(
        select(Tenant).where(
            func.lower(Tenant.slug) == slug.strip().lower()
        )
    )
    tenant = res.scalar_one_or_none()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace '{slug}' no encontrado",
        )
    if tenant.estado != "ACTIVO":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"El workspace '{tenant.nombre}' está {tenant.estado}",
        )
    return WorkspaceInfo(nombre=tenant.nombre, slug=tenant.slug)


@router.post("/login", response_model=Token, summary="CU1 - Inicio de sesión")
async def login(form: LoginRequest, db: DBDep):
    """
    Autentica al usuario y devuelve un JWT.
    - **email**: correo del usuario
    - **password**: contraseña
    """
    return await auth_service.login(form.email, form.password, db, tenant_slug=form.tenant_slug)


@router.post("/login/form", response_model=Token, include_in_schema=False)
async def login_form(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DBDep):
    """Endpoint compatible con el formulario OAuth2 de Swagger UI."""
    return await auth_service.login(form.username, form.password, db)
