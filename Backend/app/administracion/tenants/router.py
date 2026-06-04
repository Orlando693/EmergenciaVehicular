from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import CurrentUser, DBDep, require_roles
from app.administracion.tenants.schemas import TenantCreate, TenantOut, TenantUpdate
from app.administracion.tenants import service as tenant_service

router = APIRouter(
    prefix="/tenants",
    tags=["Tenants", "CU27"],
    dependencies=[Depends(require_roles("ADMINISTRADOR"))],
)


def _verificar_acceso_tenant(id_tenant_solicitado: int, current_user: CurrentUser) -> None:
    """ADMINISTRADOR solo puede gestionar su propio tenant."""
    if current_user.id_tenant != id_tenant_solicitado:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo puedes gestionar tu propio tenant",
        )


@router.get("/mi-tenant", response_model=TenantOut, summary="CU27 - Ver mi tenant")
async def mi_tenant(db: DBDep, current_user: CurrentUser):
    """Devuelve la información del tenant del usuario autenticado."""
    return await tenant_service.obtener_tenant(current_user.id_tenant, db)


@router.patch("/mi-tenant", response_model=TenantOut, summary="CU27 - Actualizar mi tenant")
async def actualizar_mi_tenant(data: TenantUpdate, db: DBDep, current_user: CurrentUser):
    """El ADMINISTRADOR actualiza únicamente la información de su propio tenant."""
    return await tenant_service.actualizar_tenant(current_user.id_tenant, data, db)


@router.get("/{id_tenant}", response_model=TenantOut, summary="Obtener tenant por ID")
async def obtener_tenant(id_tenant: int, db: DBDep, current_user: CurrentUser):
    _verificar_acceso_tenant(id_tenant, current_user)
    return await tenant_service.obtener_tenant(id_tenant, db)


@router.patch("/{id_tenant}", response_model=TenantOut, summary="Actualizar tenant por ID")
async def actualizar_tenant(id_tenant: int, data: TenantUpdate, db: DBDep, current_user: CurrentUser):
    _verificar_acceso_tenant(id_tenant, current_user)
    return await tenant_service.actualizar_tenant(id_tenant, data, db)


# Operaciones globales reservadas para SUPER_ADMIN futuro (actualmente solo via BD directa)
@router.post("", response_model=TenantOut, status_code=201, summary="Crear tenant (admin global)")
async def crear_tenant(data: TenantCreate, db: DBDep):
    return await tenant_service.crear_tenant(data, db)


@router.get("", response_model=list[TenantOut], summary="Listar todos los tenants (admin global)")
async def listar_tenants(db: DBDep):
    return await tenant_service.listar_tenants(db)
