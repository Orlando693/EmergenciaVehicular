from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant
from app.schemas.tenant import TenantCreate, TenantUpdate


async def obtener_tenant_demo(db: AsyncSession) -> Tenant:
    result = await db.execute(select(Tenant).where(Tenant.slug == "tenant-demo"))
    tenant = result.scalar_one_or_none()
    if tenant:
        return tenant

    tenant = Tenant(nombre="Tenant Demo", slug="tenant-demo", estado="ACTIVO")
    db.add(tenant)
    await db.flush()
    return tenant


async def crear_tenant(data: TenantCreate, db: AsyncSession) -> Tenant:
    slug = data.slug.strip().lower()
    existe = await db.execute(select(Tenant).where(func.lower(Tenant.slug) == slug))
    if existe.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="El slug del tenant ya existe")

    tenant = Tenant(
        nombre=data.nombre.strip(),
        slug=slug,
        estado=data.estado.strip().upper(),
    )
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return tenant


async def listar_tenants(db: AsyncSession) -> list[Tenant]:
    result = await db.execute(select(Tenant).order_by(Tenant.id_tenant.asc()))
    return list(result.scalars().all())


async def obtener_tenant(id_tenant: int, db: AsyncSession) -> Tenant:
    result = await db.execute(select(Tenant).where(Tenant.id_tenant == id_tenant))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    return tenant


async def actualizar_tenant(id_tenant: int, data: TenantUpdate, db: AsyncSession) -> Tenant:
    tenant = await obtener_tenant(id_tenant, db)
    update_data = data.model_dump(exclude_unset=True)

    if "slug" in update_data and update_data["slug"]:
        slug = update_data["slug"].strip().lower()
        existe = await db.execute(
            select(Tenant).where(func.lower(Tenant.slug) == slug, Tenant.id_tenant != id_tenant)
        )
        if existe.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="El slug del tenant ya existe")
        tenant.slug = slug

    if "nombre" in update_data and update_data["nombre"] is not None:
        tenant.nombre = update_data["nombre"].strip()
    if "estado" in update_data and update_data["estado"] is not None:
        tenant.estado = update_data["estado"].strip().upper()

    await db.commit()
    await db.refresh(tenant)
    return tenant
