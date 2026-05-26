from fastapi import APIRouter, Depends

from app.core.dependencies import DBDep, require_roles
from app.schemas.tenant import TenantCreate, TenantOut, TenantUpdate
from app.services.administracion import tenant_service

router = APIRouter(
    prefix="/tenants",
    tags=["Tenants", "CU27"],
    dependencies=[Depends(require_roles("ADMINISTRADOR"))],
)

# Nota: en produccion esta administracion global deberia moverse a un rol SUPER_ADMIN.


@router.post("", response_model=TenantOut, status_code=201)
async def crear_tenant(data: TenantCreate, db: DBDep):
    return await tenant_service.crear_tenant(data, db)


@router.get("", response_model=list[TenantOut])
async def listar_tenants(db: DBDep):
    return await tenant_service.listar_tenants(db)


@router.get("/{id_tenant}", response_model=TenantOut)
async def obtener_tenant(id_tenant: int, db: DBDep):
    return await tenant_service.obtener_tenant(id_tenant, db)


@router.patch("/{id_tenant}", response_model=TenantOut)
async def actualizar_tenant(id_tenant: int, data: TenantUpdate, db: DBDep):
    return await tenant_service.actualizar_tenant(id_tenant, data, db)
