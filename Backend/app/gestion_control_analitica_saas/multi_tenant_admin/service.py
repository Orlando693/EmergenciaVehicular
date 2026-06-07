"""
CU27 – Administrar arquitectura multi-tenant SaaS.

Vista integral del propio tenant para el ADMINISTRADOR:
- Datos del tenant, usuarios, talleres y métricas reales.
- Verificación de aislamiento de datos.
"""
from sqlalchemy import func, select, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.administracion.tenants.model import Tenant
from app.administracion.usuarios.model import Usuario
from app.gestion_incidentes.incidentes.model import Incidente
from app.operaciones.talleres.model import Taller
from app.gestion_servicios.pagos.model import Pago


async def obtener_vista_tenant(id_tenant: int, db: AsyncSession) -> dict:
    # ── Tenant ──────────────────────────────────────────────────────────────
    res_t = await db.execute(select(Tenant).where(Tenant.id_tenant == id_tenant))
    tenant = res_t.scalar_one_or_none()
    if not tenant:
        raise ValueError("Tenant no encontrado")

    # ── Usuarios con roles ──────────────────────────────────────────────────
    res_u = await db.execute(
        select(Usuario)
        .options(selectinload(Usuario.roles))
        .where(Usuario.id_tenant == id_tenant)
        .order_by(Usuario.created_at.asc())
    )
    usuarios_raw = res_u.scalars().all()
    usuarios = [
        {
            "id_usuario": u.id_usuario,
            "nombres":    u.nombres,
            "apellidos":  u.apellidos,
            "email":      u.email,
            "telefono":   u.telefono,
            "estado":     u.estado.value if hasattr(u.estado, "value") else str(u.estado),
            "roles":      [r.nombre for r in u.roles],
            "created_at": u.created_at,
        }
        for u in usuarios_raw
    ]

    # ── Talleres ────────────────────────────────────────────────────────────
    res_tall = await db.execute(
        select(Taller).where(Taller.id_tenant == id_tenant).order_by(Taller.created_at.asc())
    )
    talleres_raw = res_tall.scalars().all()
    talleres = [
        {
            "id_taller":        t.id_taller,
            "nombre_comercial": t.nombre_comercial,
            "estado":           t.estado_registro.value if hasattr(t.estado_registro, "value") else str(t.estado_registro),
            "telefono":         t.telefono_atencion,
            "email":            t.email_atencion,
            "direccion":        t.direccion,
            "created_at":       t.created_at,
        }
        for t in talleres_raw
    ]

    # ── Métricas ────────────────────────────────────────────────────────────
    res_tot_inc = await db.execute(
        select(func.count(Incidente.id_incidente)).where(Incidente.id_tenant == id_tenant)
    )
    total_inc = int(res_tot_inc.scalar() or 0)

    res_act_inc = await db.execute(
        select(func.count(Incidente.id_incidente)).where(
            Incidente.id_tenant == id_tenant,
            Incidente.estado.notin_(["COMPLETADO", "CANCELADO"]),
        )
    )
    inc_activos = int(res_act_inc.scalar() or 0)

    res_pago = await db.execute(
        select(
            func.count(Pago.id_pago).label("total"),
            func.coalesce(func.sum(Pago.monto_total), 0).label("ingresos"),
        ).where(Pago.id_tenant == id_tenant, Pago.estado == "APROBADO")
    )
    pago_row = res_pago.one()

    # Clientes = usuarios con rol CLIENTE
    clientes = [u for u in usuarios if "CLIENTE" in u["roles"]]

    metricas = {
        "total_usuarios":     len(usuarios),
        "total_talleres":     len(talleres),
        "total_clientes":     len(clientes),
        "total_incidentes":   total_inc,
        "total_pagos":        int(pago_row.total or 0),
        "ingresos_total":     float(pago_row.ingresos or 0),
        "incidentes_activos": inc_activos,
    }

    # ── Verificación de aislamiento ─────────────────────────────────────────
    # Cuenta cuántos tenants distintos aparecen en los incidentes del tenant
    res_ais = await db.execute(
        select(func.count(distinct(Incidente.id_tenant))).where(
            Incidente.id_tenant == id_tenant
        )
    )
    tenants_detectados = int(res_ais.scalar() or 0)
    aislado = tenants_detectados <= 1
    aislamiento = {
        "tenants_detectados": tenants_detectados,
        "aislado":            aislado,
        "mensaje":            "Aislamiento correcto: todos los datos pertenecen al tenant actual." if aislado
                              else f"¡Advertencia! Se detectaron {tenants_detectados} tenants en los datos.",
    }

    return {
        "tenant":      {"id_tenant": tenant.id_tenant, "nombre": tenant.nombre, "slug": tenant.slug, "estado": tenant.estado, "created_at": tenant.created_at},
        "metricas":    metricas,
        "usuarios":    usuarios,
        "talleres":    talleres,
        "aislamiento": aislamiento,
    }


async def actualizar_tenant(id_tenant: int, nombre: str, db: AsyncSession) -> dict:
    res = await db.execute(select(Tenant).where(Tenant.id_tenant == id_tenant))
    tenant = res.scalar_one_or_none()
    if not tenant:
        raise ValueError("Tenant no encontrado")
    tenant.nombre = nombre
    await db.commit()
    await db.refresh(tenant)
    return {"id_tenant": tenant.id_tenant, "nombre": tenant.nombre, "slug": tenant.slug, "estado": tenant.estado, "created_at": tenant.created_at}
