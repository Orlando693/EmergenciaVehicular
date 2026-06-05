from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.gestion_comercial_servicio.planes.model import Plan, TenantSuscripcion
from app.administracion.tenants.model import Tenant


async def listar_planes(db: AsyncSession) -> list[Plan]:
    res = await db.execute(
        select(Plan)
        .where(Plan.estado == "ACTIVO")
        .order_by(Plan.orden)
    )
    return list(res.scalars().all())


async def obtener_suscripcion_activa(id_tenant: int, db: AsyncSession) -> TenantSuscripcion | None:
    res = await db.execute(
        select(TenantSuscripcion)
        .where(
            TenantSuscripcion.id_tenant == id_tenant,
            TenantSuscripcion.estado == "ACTIVO",
        )
        .options(selectinload(TenantSuscripcion.plan))
    )
    return res.scalar_one_or_none()


async def suscribir(id_tenant: int, id_plan: int, db: AsyncSession) -> TenantSuscripcion:
    plan = await db.get(Plan, id_plan)
    if not plan or plan.estado != "ACTIVO":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan no encontrado")

    # Cancelar suscripción activa anterior
    await db.execute(
        update(TenantSuscripcion)
        .where(
            TenantSuscripcion.id_tenant == id_tenant,
            TenantSuscripcion.estado == "ACTIVO",
        )
        .values(estado="CANCELADO")
    )

    nueva = TenantSuscripcion(
        id_tenant=id_tenant,
        id_plan=id_plan,
        estado="ACTIVO",
        es_trial=(plan.precio == 0),
    )
    db.add(nueva)
    await db.flush()

    # Recargar con relación
    await db.refresh(nueva)
    res = await db.execute(
        select(TenantSuscripcion)
        .where(TenantSuscripcion.id_suscripcion == nueva.id_suscripcion)
        .options(selectinload(TenantSuscripcion.plan))
    )
    suscripcion = res.scalar_one()
    await db.commit()
    return suscripcion


async def historial_suscripciones(id_tenant: int, db: AsyncSession) -> list[TenantSuscripcion]:
    res = await db.execute(
        select(TenantSuscripcion)
        .where(TenantSuscripcion.id_tenant == id_tenant)
        .options(selectinload(TenantSuscripcion.plan))
        .order_by(TenantSuscripcion.created_at.desc())
    )
    return list(res.scalars().all())
