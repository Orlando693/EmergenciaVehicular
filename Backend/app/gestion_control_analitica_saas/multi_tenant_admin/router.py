from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.gestion_control_analitica_saas.multi_tenant_admin import service
from app.gestion_control_analitica_saas.multi_tenant_admin.schemas import (
    MultiTenantAdminOut,
    TenantInfo,
    TenantUpdate,
)

router = APIRouter(
    prefix="/multi-tenant-admin",
    tags=["multi-tenant-admin"],
    dependencies=[Depends(require_roles("ADMINISTRADOR"))],
)


@router.get("", response_model=MultiTenantAdminOut)
async def get_vista(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return await service.obtener_vista_tenant(current_user.id_tenant, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/tenant", response_model=TenantInfo)
async def actualizar_tenant(
    body: TenantUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return await service.actualizar_tenant(current_user.id_tenant, body.nombre, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
