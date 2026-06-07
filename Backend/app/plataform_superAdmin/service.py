from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import hash_password, verify_password
from app.plataform_superAdmin.model import SuperAdmin
from app.plataform_superAdmin.schemas import (
    PlanCreate, PlanUpdate, TenantCreate, TenantEstadoUpdate, TenantPlanUpdate,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _platform_token(superadmin: SuperAdmin) -> str:
    payload = {
        "sub":    str(superadmin.id_superadmin),
        "email":  superadmin.email,
        "nombre": superadmin.nombre,
        "rol":    "SUPERADMIN",
        "exp":    datetime.now(timezone.utc) + timedelta(hours=24),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_platform_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("rol") != "SUPERADMIN":
            raise HTTPException(status_code=403, detail="No es un token de plataforma")
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Token de plataforma inválido o expirado")


# ── Auth ──────────────────────────────────────────────────────────────────────

async def login_superadmin(email: str, password: str, db: AsyncSession) -> dict:
    res = await db.execute(select(SuperAdmin).where(SuperAdmin.email == email.lower().strip()))
    sa = res.scalar_one_or_none()
    if not sa or not verify_password(password, sa.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    if not sa.activo:
        raise HTTPException(status_code=403, detail="Cuenta de superadmin inactiva")
    return {
        "access_token": _platform_token(sa),
        "token_type":   "bearer",
        "nombre":       sa.nombre,
        "email":        sa.email,
        "rol":          "SUPERADMIN",
    }


# ── Tenants / Organizaciones ──────────────────────────────────────────────────

async def listar_tenants(db: AsyncSession) -> list:
    from app.administracion.tenants.model import Tenant
    from app.gestion_comercial_servicio.planes.model import Plan, TenantSuscripcion

    res = await db.execute(select(Tenant).order_by(Tenant.created_at.desc()))
    tenants = res.scalars().all()

    result = []
    for t in tenants:
        sus = await db.execute(
            select(TenantSuscripcion).where(
                TenantSuscripcion.id_tenant == t.id_tenant,
                TenantSuscripcion.estado == "ACTIVO",
            )
        )
        sus_obj = sus.scalar_one_or_none()
        plan_nombre = plan_slug = None
        if sus_obj:
            plan_res = await db.execute(select(Plan).where(Plan.id_plan == sus_obj.id_plan))
            plan = plan_res.scalar_one_or_none()
            if plan:
                plan_nombre = plan.nombre
                plan_slug   = plan.slug

        result.append({
            "id_tenant":   t.id_tenant,
            "nombre":      t.nombre,
            "slug":        t.slug,
            "estado":      t.estado,
            "plan_nombre": plan_nombre,
            "plan_slug":   plan_slug,
            "created_at":  t.created_at,
        })
    return result


async def crear_tenant(data: TenantCreate, db: AsyncSession):
    from app.administracion.tenants.model import Tenant
    from app.gestion_comercial_servicio.planes.model import TenantSuscripcion

    dup = await db.execute(select(Tenant).where(Tenant.slug == data.slug.lower().strip()))
    if dup.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Ya existe un tenant con ese slug")

    tenant = Tenant(nombre=data.nombre, slug=data.slug.lower().strip(), estado="ACTIVO")
    db.add(tenant)
    await db.flush()

    if data.id_plan:
        sus = TenantSuscripcion(id_tenant=tenant.id_tenant, id_plan=data.id_plan, estado="ACTIVO")
        db.add(sus)

    await db.commit()
    await db.refresh(tenant)
    return tenant


async def cambiar_estado_tenant(id_tenant: int, data: TenantEstadoUpdate, db: AsyncSession):
    from app.administracion.tenants.model import Tenant

    res = await db.execute(select(Tenant).where(Tenant.id_tenant == id_tenant))
    tenant = res.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    tenant.estado = data.estado
    await db.commit()
    await db.refresh(tenant)
    return tenant


async def asignar_plan_tenant(id_tenant: int, data: TenantPlanUpdate, db: AsyncSession):
    from app.gestion_comercial_servicio.planes.model import TenantSuscripcion

    sus_res = await db.execute(
        select(TenantSuscripcion).where(
            TenantSuscripcion.id_tenant == id_tenant,
            TenantSuscripcion.estado == "ACTIVO",
        )
    )
    sus = sus_res.scalar_one_or_none()
    if sus:
        sus.estado = "CANCELADO"

    nueva = TenantSuscripcion(id_tenant=id_tenant, id_plan=data.id_plan, estado="ACTIVO")
    db.add(nueva)
    await db.commit()
    await db.refresh(nueva)
    return nueva


# ── Planes ────────────────────────────────────────────────────────────────────

async def listar_planes(db: AsyncSession) -> list:
    from app.gestion_comercial_servicio.planes.model import Plan

    res = await db.execute(select(Plan).order_by(Plan.orden))
    return res.scalars().all()


async def crear_plan(data: PlanCreate, db: AsyncSession):
    from app.gestion_comercial_servicio.planes.model import Plan

    plan = Plan(**data.model_dump(), estado="ACTIVO", moneda="BOB")
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan


async def actualizar_plan(id_plan: int, data: PlanUpdate, db: AsyncSession):
    from app.gestion_comercial_servicio.planes.model import Plan

    res = await db.execute(select(Plan).where(Plan.id_plan == id_plan))
    plan = res.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    for k, v in data.model_dump().items():
        setattr(plan, k, v)
    await db.commit()
    await db.refresh(plan)
    return plan
