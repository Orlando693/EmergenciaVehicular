from datetime import datetime, timedelta

from sqlalchemy import func, select, case, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.gestion_incidentes.incidentes.model import Incidente
from app.operaciones.talleres.model import Taller
from app.operaciones.tecnicos.model import Tecnico
from app.administracion.usuarios.model import Cliente
from app.gestion_servicios.pagos.model import Pago


async def obtener_dashboard(
    id_tenant: int,
    db: AsyncSession,
    fecha_desde: datetime | None = None,
    fecha_hasta: datetime | None = None,
    id_taller: int | None = None,
    clasificacion: str | None = None,
) -> dict:

    # Rango de fechas por defecto: últimos 30 días
    if not fecha_hasta:
        fecha_hasta = datetime.utcnow()
    if not fecha_desde:
        fecha_desde = fecha_hasta - timedelta(days=30)

    # ── Filtro base de incidentes ─────────────────────────────────────────
    filtros = [
        Incidente.id_tenant == id_tenant,
        Incidente.created_at >= fecha_desde,
        Incidente.created_at <= fecha_hasta,
    ]
    if id_taller:
        filtros.append(Incidente.id_taller == id_taller)
    if clasificacion:
        filtros.append(Incidente.clasificacion_ia == clasificacion)

    # ── KPIs de incidentes ────────────────────────────────────────────────
    res_totales = await db.execute(
        select(
            func.count(Incidente.id_incidente).label("total"),
            func.sum(case((Incidente.estado.in_(["REPORTADO", "ASIGNADO", "EN_CAMINO", "EN_ATENCION"]), 1), else_=0)).label("activos"),
            func.sum(case((Incidente.estado == "COMPLETADO", 1), else_=0)).label("completados"),
            func.sum(case((Incidente.estado == "CANCELADO", 1), else_=0)).label("cancelados"),
        ).where(and_(*filtros))
    )
    row = res_totales.one()
    total_inc    = int(row.total or 0)
    activos      = int(row.activos or 0)
    completados  = int(row.completados or 0)
    cancelados   = int(row.cancelados or 0)

    # ── Talleres ──────────────────────────────────────────────────────────
    res_talleres = await db.execute(
        select(func.count(Taller.id_taller)).where(Taller.id_tenant == id_tenant)
    )
    total_talleres = int(res_talleres.scalar() or 0)

    # ── Técnicos ──────────────────────────────────────────────────────────
    res_tec = await db.execute(
        select(func.count(Tecnico.id_tecnico)).where(
            Tecnico.id_tenant == id_tenant,
            Tecnico.activo == True,  # noqa: E712
        )
    )
    total_tecnicos = int(res_tec.scalar() or 0)

    # ── Clientes ──────────────────────────────────────────────────────────
    res_cli = await db.execute(
        select(func.count(Cliente.id_cliente)).where(Cliente.id_tenant == id_tenant)
    )
    total_clientes = int(res_cli.scalar() or 0)

    # ── Ingresos (pagos COMPLETADO) ───────────────────────────────────────
    res_ing = await db.execute(
        select(func.coalesce(func.sum(Pago.monto_total), 0)).where(
            Pago.id_tenant == id_tenant,
            Pago.estado == "COMPLETADO",
            Pago.created_at >= fecha_desde,
            Pago.created_at <= fecha_hasta,
        )
    )
    ingresos_totales = float(res_ing.scalar() or 0)

    # ── Cumplimiento SLA ──────────────────────────────────────────────────
    cumplimiento_sla = round((completados / total_inc * 100) if total_inc > 0 else 0, 1)

    # ── Por estado ────────────────────────────────────────────────────────
    res_estado = await db.execute(
        select(Incidente.estado, func.count(Incidente.id_incidente).label("c"))
        .where(and_(*filtros))
        .group_by(Incidente.estado)
        .order_by(func.count(Incidente.id_incidente).desc())
    )
    por_estado = [{"nombre": r.estado, "total": r.c} for r in res_estado.all()]

    # ── Por clasificación IA ──────────────────────────────────────────────
    res_clas = await db.execute(
        select(
            Incidente.clasificacion_ia,
            func.count(Incidente.id_incidente).label("c"),
        )
        .where(and_(*filtros))
        .group_by(Incidente.clasificacion_ia)
        .order_by(func.count(Incidente.id_incidente).desc())
        .limit(8)
    )
    por_clasificacion = [
        {"nombre": r.clasificacion_ia or "Sin clasificar", "total": r.c}
        for r in res_clas.all()
    ]

    # ── Métricas por taller ───────────────────────────────────────────────
    res_taller_met = await db.execute(
        select(
            Taller.nombre_comercial,
            func.count(Incidente.id_incidente).label("total"),
            func.sum(case((Incidente.estado == "COMPLETADO", 1), else_=0)).label("comp"),
            func.sum(case((Incidente.estado == "CANCELADO", 1), else_=0)).label("canc"),
        )
        .join(Incidente, Incidente.id_taller == Taller.id_taller, isouter=True)
        .where(
            Taller.id_tenant == id_tenant,
            and_(
                Incidente.created_at >= fecha_desde,
                Incidente.created_at <= fecha_hasta,
            ) if True else True,
        )
        .group_by(Taller.id_taller, Taller.nombre_comercial)
        .order_by(func.count(Incidente.id_incidente).desc())
        .limit(10)
    )
    por_taller = []
    for r in res_taller_met.all():
        tot = int(r.total or 0)
        comp = int(r.comp or 0)
        canc = int(r.canc or 0)
        tasa = round(comp / tot * 100, 1) if tot > 0 else 0
        por_taller.append({
            "nombre": r.nombre_comercial,
            "total_incidentes": tot,
            "completados": comp,
            "cancelados": canc,
            "tasa_cumplimiento": tasa,
        })

    # ── Tendencia 7 días ──────────────────────────────────────────────────
    from sqlalchemy import text as sa_text
    hace7 = fecha_hasta - timedelta(days=6)
    _dia_col = func.date_trunc(sa_text("'day'"), Incidente.created_at).label("dia")
    res_tend = await db.execute(
        select(_dia_col, func.count(Incidente.id_incidente).label("c"))
        .where(
            Incidente.id_tenant == id_tenant,
            Incidente.created_at >= hace7,
            Incidente.created_at <= fecha_hasta,
        )
        .group_by(sa_text("1"))
        .order_by(sa_text("1"))
    )
    dias_map: dict[str, int] = {str(r.dia)[:10]: r.c for r in res_tend.all()}
    tendencia_7dias = []
    for i in range(7):
        d = (hace7 + timedelta(days=i)).date()
        tendencia_7dias.append({"fecha": str(d), "total": dias_map.get(str(d), 0)})

    return {
        "total_incidentes":       total_inc,
        "incidentes_activos":     activos,
        "incidentes_completados": completados,
        "incidentes_cancelados":  cancelados,
        "total_talleres":         total_talleres,
        "total_tecnicos":         total_tecnicos,
        "total_clientes":         total_clientes,
        "ingresos_totales":       ingresos_totales,
        "cumplimiento_sla":       cumplimiento_sla,
        "por_estado":             por_estado,
        "por_clasificacion":      por_clasificacion,
        "por_taller":             por_taller,
        "tendencia_7dias":        tendencia_7dias,
    }
