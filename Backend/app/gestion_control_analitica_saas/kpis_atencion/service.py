"""
CU25 – Analizar KPIs de atención del servicio.

Calcula indicadores sobre el flujo real:
REPORTADO → EN_PROCESO → RESUELTO → PAGADO, con CANCELADO como salida.
"""
from datetime import datetime, timedelta

from sqlalchemy import func, select, case, and_, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.gestion_incidentes.incidentes.model import Incidente, IncidenteHistorial
from app.operaciones.talleres.model import Taller


async def obtener_kpis(
    id_tenant: int,
    db: AsyncSession,
    fecha_desde: datetime | None = None,
    fecha_hasta: datetime | None = None,
    id_taller: int | None = None,
    clasificacion: str | None = None,
) -> dict:

    if not fecha_hasta:
        fecha_hasta = datetime.utcnow()
    if not fecha_desde:
        fecha_desde = fecha_hasta - timedelta(days=30)

    # ── Filtro base de incidentes ─────────────────────────────────────────
    filtros_inc = [
        Incidente.id_tenant == id_tenant,
        Incidente.created_at >= fecha_desde,
        Incidente.created_at <= fecha_hasta,
    ]
    if id_taller:
        filtros_inc.append(Incidente.id_taller == id_taller)
    if clasificacion:
        filtros_inc.append(Incidente.clasificacion_ia == clasificacion)

    # ── Totales generales ─────────────────────────────────────────────────
    res_tot = await db.execute(
        select(
            func.count(Incidente.id_incidente).label("total"),
            func.sum(case((Incidente.id_taller.is_not(None), 1), else_=0)).label("asignados"),
            func.sum(case((Incidente.estado.in_(["RESUELTO", "PAGADO"]), 1), else_=0)).label("completados"),
            func.sum(case((Incidente.estado == "CANCELADO", 1), else_=0)).label("cancelados"),
        ).where(and_(*filtros_inc))
    )
    row = res_tot.one()
    total_inc    = int(row.total       or 0)
    total_asig   = int(row.asignados   or 0)
    total_comp   = int(row.completados or 0)
    total_canc   = int(row.cancelados  or 0)

    # El sistema registra EN_PROCESO cuando el taller acepta/inicia la atención.
    avg_inicio = await _avg_transicion(db, id_tenant, filtros_inc, ["EN_PROCESO"])
    avg_resolucion = await _avg_resolucion_total(db, id_tenant, filtros_inc)

    tiempos = [
        {"label": "Inicio de atención", "minutos": avg_inicio, "descripcion": "Desde que se reporta hasta que el taller inicia el servicio"},
        {"label": "Resolución total", "minutos": avg_resolucion, "descripcion": "Desde que se reporta hasta que queda resuelto o pagado"},
    ]

    # ── SLA: objetivo 80 % completados ───────────────────────────────────
    sla_pct = round(total_comp / total_inc * 100, 1) if total_inc > 0 else 0
    if sla_pct >= 80:
        nivel = "EXCELENTE"
    elif sla_pct >= 60:
        nivel = "BUENO"
    elif sla_pct >= 40:
        nivel = "REGULAR"
    else:
        nivel = "BAJO"

    sla = {
        "nivel":       nivel,
        "porcentaje":  sla_pct,
        "completados": total_comp,
        "total":       total_inc,
        "objetivo":    80.0,
    }

    # ── Tasas ─────────────────────────────────────────────────────────────
    tasa_asignacion = round(total_asig / total_inc * 100, 1) if total_inc > 0 else 0
    # Abandono: incidentes cancelados después de tener un taller asignado.
    res_aband = await db.execute(
        select(func.count(Incidente.id_incidente)).where(
            and_(*filtros_inc),
            Incidente.id_taller.is_not(None),
            Incidente.estado == "CANCELADO",
        )
    )
    abandono_cnt = int(res_aband.scalar() or 0)
    tasa_abandono = round(abandono_cnt / total_asig * 100, 1) if total_asig > 0 else 0

    # ── Eficiencia por taller ─────────────────────────────────────────────
    res_tall = await db.execute(
        select(
            Taller.nombre_comercial,
            func.count(Incidente.id_incidente).label("total"),
            func.sum(case((Incidente.estado.in_(["RESUELTO", "PAGADO"]), 1), else_=0)).label("comp"),
        )
        .join(Incidente, Incidente.id_taller == Taller.id_taller, isouter=True)
        .where(
            Taller.id_tenant == id_tenant,
            Incidente.created_at >= fecha_desde,
            Incidente.created_at <= fecha_hasta,
            *(([Incidente.clasificacion_ia == clasificacion]) if clasificacion else []),
        )
        .group_by(Taller.id_taller, Taller.nombre_comercial)
        .order_by(func.count(Incidente.id_incidente).desc())
        .limit(10)
    )

    talleres = []
    for r in res_tall.all():
        tot = int(r.total or 0)
        comp = int(r.comp or 0)
        tasa = round(comp / tot * 100, 1) if tot > 0 else 0
        # tiempo promedio de resolución por taller
        avg_t = await _avg_resolucion_taller(db, id_tenant, Taller.id_taller if False else None, r.nombre_comercial, fecha_desde, fecha_hasta)
        talleres.append({
            "nombre":                 r.nombre_comercial,
            "total_asignados":        tot,
            "total_completados":      comp,
            "avg_minutos_resolucion": avg_t,
            "tasa_cumplimiento":      tasa,
        })

    return {
        "tiempos":            tiempos,
        "sla":                sla,
        "tasa_asignacion":    tasa_asignacion,
        "tasa_abandono":      tasa_abandono,
        "talleres":           talleres,
        "total_incidentes":   total_inc,
        "total_asignados":    total_asig,
        "total_completados":  total_comp,
        "total_cancelados":   total_canc,
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _avg_transicion(
    db: AsyncSession,
    id_tenant: int,
    filtros_inc: list,
    estados_nuevos: list[str],
) -> float | None:
    """
    Calcula el tiempo promedio (en minutos) desde la creación del incidente
    hasta que alcanzó cualquiera de los estados indicados por primera vez.
    """
    # Subconsulta: min(created_at) de historial donde estado_nuevo = X para cada incidente del tenant
    sub = (
        select(
            IncidenteHistorial.id_incidente,
            func.min(IncidenteHistorial.created_at).label("ts"),
        )
        .where(
            IncidenteHistorial.id_tenant == id_tenant,
            IncidenteHistorial.estado_nuevo.in_(estados_nuevos),
        )
        .group_by(IncidenteHistorial.id_incidente)
        .subquery()
    )

    res = await db.execute(
        select(
            func.avg(
                func.extract("epoch", sub.c.ts - Incidente.created_at) / 60
            ).label("avg_min")
        )
        .join(sub, sub.c.id_incidente == Incidente.id_incidente)
        .where(and_(*filtros_inc))
    )
    val = res.scalar()
    return round(float(val), 1) if val is not None else None


async def _avg_resolucion_total(
    db: AsyncSession,
    id_tenant: int,
    filtros_inc: list,
) -> float | None:
    sub = (
        select(
            IncidenteHistorial.id_incidente,
            func.min(IncidenteHistorial.created_at).label("ts_comp"),
        )
        .where(
            IncidenteHistorial.id_tenant == id_tenant,
            IncidenteHistorial.estado_nuevo.in_(["RESUELTO", "PAGADO"]),
        )
        .group_by(IncidenteHistorial.id_incidente)
        .subquery()
    )

    res = await db.execute(
        select(
            func.avg(
                func.extract("epoch", sub.c.ts_comp - Incidente.created_at) / 60
            ).label("avg_min")
        )
        .join(sub, sub.c.id_incidente == Incidente.id_incidente)
        .where(and_(*filtros_inc))
    )
    val = res.scalar()
    return round(float(val), 1) if val is not None else None


async def _avg_resolucion_taller(
    db: AsyncSession,
    id_tenant: int,
    _unused,
    nombre_comercial: str,
    fecha_desde: datetime,
    fecha_hasta: datetime,
) -> float | None:
    sub_comp = (
        select(
            IncidenteHistorial.id_incidente,
            func.min(IncidenteHistorial.created_at).label("ts_comp"),
        )
        .where(
            IncidenteHistorial.id_tenant == id_tenant,
            IncidenteHistorial.estado_nuevo.in_(["RESUELTO", "PAGADO"]),
            IncidenteHistorial.created_at >= fecha_desde,
            IncidenteHistorial.created_at <= fecha_hasta,
        )
        .group_by(IncidenteHistorial.id_incidente)
        .subquery()
    )

    res = await db.execute(
        select(
            func.avg(
                func.extract("epoch", sub_comp.c.ts_comp - Incidente.created_at) / 60
            ).label("avg_min")
        )
        .join(sub_comp, sub_comp.c.id_incidente == Incidente.id_incidente)
        .join(Taller, Taller.id_taller == Incidente.id_taller)
        .where(
            Incidente.id_tenant == id_tenant,
            Taller.nombre_comercial == nombre_comercial,
            Incidente.created_at >= fecha_desde,
            Incidente.created_at <= fecha_hasta,
        )
    )
    val = res.scalar()
    return round(float(val), 1) if val is not None else None
