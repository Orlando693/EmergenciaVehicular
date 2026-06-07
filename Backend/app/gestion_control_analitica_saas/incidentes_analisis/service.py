"""
CU26 – Analizar incidentes por tipo, zona y estado.

Agrupa incidentes reales del tenant por clasificacion_ia, direccion/zona y estado.
"""
from datetime import datetime, timedelta

from sqlalchemy import func, select, and_, case, text, literal_column
from sqlalchemy.ext.asyncio import AsyncSession

from app.gestion_incidentes.incidentes.model import Incidente

ESTADOS_ORDEN = ["REPORTADO", "ASIGNADO", "EN_CAMINO", "EN_ATENCION", "COMPLETADO", "CANCELADO"]


async def obtener_analisis(
    id_tenant:     int,
    db:            AsyncSession,
    fecha_desde:   datetime | None = None,
    fecha_hasta:   datetime | None = None,
    tipo:          str | None = None,
    estado:        str | None = None,
    zona:          str | None = None,
) -> dict:

    if not fecha_hasta:
        fecha_hasta = datetime.utcnow()
    if not fecha_desde:
        fecha_desde = fecha_hasta - timedelta(days=30)

    filtros = [
        Incidente.id_tenant == id_tenant,
        Incidente.created_at >= fecha_desde,
        Incidente.created_at <= fecha_hasta,
    ]
    if tipo:
        filtros.append(Incidente.clasificacion_ia == tipo)
    if estado:
        filtros.append(Incidente.estado == estado)
    if zona:
        filtros.append(Incidente.direccion.ilike(f"%{zona}%"))

    # ── Total general ──────────────────────────────────────────────────────
    res_tot = await db.execute(
        select(func.count(Incidente.id_incidente)).where(and_(*filtros))
    )
    total = int(res_tot.scalar() or 0)

    # ── Por estado ─────────────────────────────────────────────────────────
    res_est = await db.execute(
        select(Incidente.estado, func.count(Incidente.id_incidente).label("cnt"))
        .where(and_(*filtros))
        .group_by(Incidente.estado)
        .order_by(func.count(Incidente.id_incidente).desc())
    )
    por_estado = [
        {"nombre": r.estado, "total": int(r.cnt), "pct": round(int(r.cnt) / total * 100, 1) if total else 0}
        for r in res_est.all()
    ]
    # Garantizar todos los estados en el orden canónico
    est_map = {e["nombre"]: e for e in por_estado}
    por_estado = [
        est_map.get(e, {"nombre": e, "total": 0, "pct": 0.0})
        for e in ESTADOS_ORDEN
    ]

    # ── Por tipo / clasificación IA ────────────────────────────────────────
    res_tipo = await db.execute(
        select(
            Incidente.clasificacion_ia,
            func.count(Incidente.id_incidente).label("cnt"),
        )
        .where(and_(*filtros))
        .group_by(Incidente.clasificacion_ia)
        .order_by(func.count(Incidente.id_incidente).desc())
        .limit(15)
    )
    por_tipo = [
        {"nombre": r.clasificacion_ia or "Sin clasificar", "total": int(r.cnt), "pct": round(int(r.cnt) / total * 100, 1) if total else 0}
        for r in res_tipo.all()
    ]

    # ── Por zona (primera parte de dirección) ──────────────────────────────
    # Extrae el segmento antes de la primera coma como "zona"
    zona_expr = func.btrim(func.split_part(
        func.coalesce(Incidente.direccion, "Sin zona"), ",", 1
    ))
    res_zona = await db.execute(
        select(zona_expr.label("zona"), func.count(Incidente.id_incidente).label("cnt"))
        .where(and_(*filtros))
        .group_by(zona_expr)
        .order_by(func.count(Incidente.id_incidente).desc())
        .limit(10)
    )
    por_zona = [
        {"zona": r.zona or "Sin zona", "total": int(r.cnt), "pct": round(int(r.cnt) / total * 100, 1) if total else 0}
        for r in res_zona.all()
    ]

    # ── Tendencia diaria ───────────────────────────────────────────────────
    _dia = func.date_trunc(text("'day'"), Incidente.created_at).label("dia")
    res_tend = await db.execute(
        select(_dia, func.count(Incidente.id_incidente).label("cnt"))
        .where(and_(*filtros))
        .group_by(text("1"))
        .order_by(text("1"))
    )
    tendencia = [
        {"fecha": str(r.dia)[:10], "total": int(r.cnt)}
        for r in res_tend.all()
    ]

    # ── Cruce tipo × estado ────────────────────────────────────────────────
    # Para los top 5 tipos, listar cuántos por cada estado
    top5_tipos = [t["nombre"] for t in por_tipo[:5]]
    cruce = []
    for tp in top5_tipos:
        filtros_cruce = filtros + [
            func.coalesce(Incidente.clasificacion_ia, "Sin clasificar") == tp
        ]
        res_cr = await db.execute(
            select(Incidente.estado, func.count(Incidente.id_incidente).label("cnt"))
            .where(and_(*filtros_cruce))
            .group_by(Incidente.estado)
        )
        estados_dict: dict[str, int] = {r.estado: int(r.cnt) for r in res_cr.all()}
        cruce.append({"tipo": tp, "estados": estados_dict})

    return {
        "total":             total,
        "por_estado":        por_estado,
        "por_tipo":          por_tipo,
        "por_zona":          por_zona,
        "tendencia":         tendencia,
        "cruce_tipo_estado": cruce,
    }
