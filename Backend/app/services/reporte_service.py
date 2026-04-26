from datetime import datetime
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.incidente import Incidente
from app.models.taller import Taller
from app.models.cliente import Cliente
from app.models.usuario import Usuario
from app.models.pago import Pago
from app.schemas.reporte import (
    ResumenGeneral, ReporteIncidentes, ItemIncidente,
    ReporteUsuarios, ItemUsuario,
    ReporteTalleres, ItemTaller,
    ReportePagos, ItemPago,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


# ── Resumen general ───────────────────────────────────────────────────────────

async def resumen_general(db: AsyncSession) -> ResumenGeneral:
    # Incidentes por estado
    estados = ["REPORTADO", "EN_PROCESO", "RESUELTO", "PAGADO", "CANCELADO"]
    conteos: dict[str, int] = {}
    for est in estados:
        r = await db.execute(
            select(func.count()).where(Incidente.estado == est).select_from(Incidente)
        )
        conteos[est] = r.scalar_one()
    total_inc = sum(conteos.values())

    # Usuarios y clientes
    r_users   = await db.execute(select(func.count()).select_from(Usuario))
    r_clients = await db.execute(select(func.count()).select_from(Cliente))
    r_talleres = await db.execute(
        select(func.count()).where(Taller.estado_registro == "APROBADO").select_from(Taller)
    )

    # Pagos
    r_pagos = await db.execute(
        select(func.count()).where(Pago.estado == "COMPLETADO").select_from(Pago)
    )
    r_ingresos = await db.execute(
        select(func.sum(Pago.monto_total)).where(Pago.estado == "COMPLETADO")
    )
    r_comision = await db.execute(
        select(func.sum(Pago.comision_plataforma)).where(Pago.estado == "COMPLETADO")
    )

    return ResumenGeneral(
        total_incidentes=total_inc,
        incidentes_reportados=conteos.get("REPORTADO", 0),
        incidentes_en_proceso=conteos.get("EN_PROCESO", 0),
        incidentes_resueltos=conteos.get("RESUELTO", 0),
        incidentes_pagados=conteos.get("PAGADO", 0),
        incidentes_cancelados=conteos.get("CANCELADO", 0),
        total_usuarios=r_users.scalar_one(),
        total_clientes=r_clients.scalar_one(),
        total_talleres=r_talleres.scalar_one(),
        total_pagos_completados=r_pagos.scalar_one(),
        ingresos_totales=Decimal(str(r_ingresos.scalar_one() or 0)),
        comision_plataforma_total=Decimal(str(r_comision.scalar_one() or 0)),
    )


# ── Incidentes ────────────────────────────────────────────────────────────────

async def reporte_incidentes(
    db: AsyncSession,
    desde: str | None = None,
    hasta: str | None = None,
    estado: str | None = None,
    id_taller: int | None = None,
) -> ReporteIncidentes:
    stmt = select(Incidente, Taller.razon_social).outerjoin(Taller, Incidente.id_taller == Taller.id_taller)

    if _parse_dt(desde):
        stmt = stmt.where(Incidente.created_at >= _parse_dt(desde))
    if _parse_dt(hasta):
        stmt = stmt.where(Incidente.created_at <= _parse_dt(hasta))
    if estado:
        stmt = stmt.where(Incidente.estado == estado)
    if id_taller:
        stmt = stmt.where(Incidente.id_taller == id_taller)

    stmt = stmt.order_by(Incidente.created_at.desc())
    result = await db.execute(stmt)
    rows = result.all()

    items = [
        ItemIncidente(
            id_incidente=inc.id_incidente,
            clasificacion_ia=inc.clasificacion_ia,
            estado=inc.estado,
            taller_nombre=taller_nombre,
            direccion=inc.direccion,
            created_at=inc.created_at,
        )
        for inc, taller_nombre in rows
    ]

    por_estado: dict[str, int] = {}
    for item in items:
        por_estado[item.estado] = por_estado.get(item.estado, 0) + 1

    return ReporteIncidentes(items=items, total=len(items), por_estado=por_estado)


# ── Usuarios ──────────────────────────────────────────────────────────────────

async def reporte_usuarios(
    db: AsyncSession,
    desde: str | None = None,
    hasta: str | None = None,
    rol: str | None = None,
) -> ReporteUsuarios:
    stmt = (
        select(Usuario)
        .options(selectinload(Usuario.roles))
        .order_by(Usuario.created_at.desc())
    )
    if _parse_dt(desde):
        stmt = stmt.where(Usuario.created_at >= _parse_dt(desde))
    if _parse_dt(hasta):
        stmt = stmt.where(Usuario.created_at <= _parse_dt(hasta))

    result = await db.execute(stmt)
    usuarios = result.scalars().all()

    items: list[ItemUsuario] = []
    for u in usuarios:
        roles_nombres = [r.nombre for r in u.roles]
        if rol and rol not in roles_nombres:
            continue
        rol_str = roles_nombres[0] if roles_nombres else "SIN ROL"
        items.append(ItemUsuario(
            id_usuario=u.id_usuario,
            nombres=u.nombres,
            apellidos=u.apellidos,
            email=u.email,
            rol=rol_str,
            estado=u.estado.value,
            created_at=u.created_at,
        ))

    por_rol: dict[str, int] = {}
    for it in items:
        por_rol[it.rol] = por_rol.get(it.rol, 0) + 1

    return ReporteUsuarios(items=items, total=len(items), por_rol=por_rol)


# ── Talleres ──────────────────────────────────────────────────────────────────

async def reporte_talleres(db: AsyncSession) -> ReporteTalleres:
    talleres_r = await db.execute(select(Taller))
    talleres = talleres_r.scalars().all()

    items: list[ItemTaller] = []
    total_ingresos = Decimal("0")

    for t in talleres:
        # Servicios totales (incidentes asignados)
        r_total = await db.execute(
            select(func.count()).where(Incidente.id_taller == t.id_taller).select_from(Incidente)
        )
        total_svc = r_total.scalar_one()

        r_comp = await db.execute(
            select(func.count()).where(
                Incidente.id_taller == t.id_taller,
                Incidente.estado.in_(["RESUELTO", "PAGADO"])
            ).select_from(Incidente)
        )
        comp_svc = r_comp.scalar_one()

        # Ingresos del taller (de pagos completados)
        sub_inc = select(Incidente.id_incidente).where(Incidente.id_taller == t.id_taller)
        r_ing = await db.execute(
            select(func.sum(Pago.monto_taller)).where(
                Pago.id_incidente.in_(sub_inc),
                Pago.estado == "COMPLETADO"
            )
        )
        ing = Decimal(str(r_ing.scalar_one() or 0))
        total_ingresos += ing

        items.append(ItemTaller(
            id_taller=t.id_taller,
            razon_social=t.razon_social,
            estado_registro=t.estado_registro,
            total_servicios=total_svc,
            servicios_completados=comp_svc,
            ingresos_taller=ing,
        ))

    return ReporteTalleres(items=items, total=len(items), total_ingresos=total_ingresos)


# ── Pagos ─────────────────────────────────────────────────────────────────────

async def reporte_pagos(
    db: AsyncSession,
    desde: str | None = None,
    hasta: str | None = None,
    estado: str | None = None,
    metodo: str | None = None,
) -> ReportePagos:
    stmt = select(Pago).order_by(Pago.created_at.desc())

    if _parse_dt(desde):
        stmt = stmt.where(Pago.created_at >= _parse_dt(desde))
    if _parse_dt(hasta):
        stmt = stmt.where(Pago.created_at <= _parse_dt(hasta))
    if estado:
        stmt = stmt.where(Pago.estado == estado)
    if metodo:
        stmt = stmt.where(Pago.metodo_pago == metodo.upper())

    result = await db.execute(stmt)
    pagos = result.scalars().all()

    items = [ItemPago.model_validate(p) for p in pagos]

    monto_total   = sum((it.monto_total for it in items), Decimal("0"))
    comision_total = sum((it.comision_plataforma for it in items), Decimal("0"))

    por_metodo: dict[str, int] = {}
    por_estado: dict[str, int] = {}
    for it in items:
        por_metodo[it.metodo_pago] = por_metodo.get(it.metodo_pago, 0) + 1
        por_estado[it.estado]      = por_estado.get(it.estado, 0) + 1

    return ReportePagos(
        items=items,
        total=len(items),
        monto_total=monto_total,
        comision_total=comision_total,
        por_metodo=por_metodo,
        por_estado=por_estado,
    )
