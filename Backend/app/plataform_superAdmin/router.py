from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.plataform_superAdmin import service
from app.plataform_superAdmin.schemas import (
    PlanCreate, PlanPlatformOut, PlanUpdate,
    PlatformLoginRequest, PlatformTokenResponse,
    TenantCreate, TenantEstadoUpdate, TenantPlatformOut, TenantPlanUpdate,
)

router = APIRouter(prefix="/platform", tags=["platform-superadmin"])


# ── Dependency: valida token de plataforma ────────────────────────────────────

async def get_current_superadmin(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.split(" ", 1)[1]
    return service.verify_platform_token(token)


# ── Auth ──────────────────────────────────────────────────────────────────────

@router.post("/auth/login", response_model=PlatformTokenResponse)
async def login(body: PlatformLoginRequest, db: AsyncSession = Depends(get_db)):
    return await service.login_superadmin(body.email, body.password, db)


# ── Tenants / Organizaciones ──────────────────────────────────────────────────

@router.get("/tenants", response_model=list[TenantPlatformOut])
async def get_tenants(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_superadmin),
):
    return await service.listar_tenants(db)


@router.post("/tenants", response_model=TenantPlatformOut, status_code=201)
async def crear_tenant(
    body: TenantCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_superadmin),
):
    return await service.crear_tenant(body, db)


@router.patch("/tenants/{id_tenant}/estado", response_model=TenantPlatformOut)
async def cambiar_estado(
    id_tenant: int,
    body: TenantEstadoUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_superadmin),
):
    return await service.cambiar_estado_tenant(id_tenant, body, db)


@router.patch("/tenants/{id_tenant}/plan")
async def asignar_plan(
    id_tenant: int,
    body: TenantPlanUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_superadmin),
):
    return await service.asignar_plan_tenant(id_tenant, body, db)


# ── Planes ────────────────────────────────────────────────────────────────────

@router.get("/planes", response_model=list[PlanPlatformOut])
async def get_planes(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_superadmin),
):
    return await service.listar_planes(db)


@router.post("/planes", response_model=PlanPlatformOut, status_code=201)
async def nuevo_plan(
    body: PlanCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_superadmin),
):
    return await service.crear_plan(body, db)


@router.put("/planes/{id_plan}", response_model=PlanPlatformOut)
async def editar_plan(
    id_plan: int,
    body: PlanUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_superadmin),
):
    return await service.actualizar_plan(id_plan, body, db)
