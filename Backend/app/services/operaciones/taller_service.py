from fastapi import HTTPException, status
from decimal import Decimal
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.taller import Taller
from app.models.incidente import Incidente
from app.models.pago import Pago
from app.models.usuario import Usuario, Rol, UsuarioRol
from app.models.enums import EstadoTallerEnum
from app.schemas.taller import TallerCreate, TallerUpdate, TallerOut, TallerEstadoUpdate
from app.core.security import hash_password


async def registrar_taller(
    id_usuario: int,
    data: TallerCreate,
    db: AsyncSession,
) -> TallerOut:
    existe = await db.execute(select(Taller).where(Taller.id_usuario == id_usuario))
    if existe.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Este usuario ya tiene un taller registrado")

    if data.nit:
        dup = await db.execute(select(Taller).where(Taller.nit == data.nit))
        if dup.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="El NIT ya está registrado")

    taller = Taller(id_usuario=id_usuario, **data.model_dump())
    db.add(taller)
    await db.commit()
    await db.refresh(taller)
    return taller


async def listar_talleres(
    db: AsyncSession,
    estado: EstadoTallerEnum | None = None,
) -> list[TallerOut]:
    query = select(Taller)
    if estado:
        query = query.where(Taller.estado_registro == estado)
    result = await db.execute(query)
    return result.scalars().all()


async def obtener_taller(id_taller: int, db: AsyncSession) -> TallerOut:
    result = await db.execute(select(Taller).where(Taller.id_taller == id_taller))
    taller = result.scalar_one_or_none()
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado")
    return taller


async def obtener_taller_por_usuario(id_usuario: int, db: AsyncSession) -> TallerOut:
    result = await db.execute(select(Taller).where(Taller.id_usuario == id_usuario))
    taller = result.scalar_one_or_none()
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado para este usuario")
    return taller


async def actualizar_taller(id_taller: int, data: TallerUpdate, db: AsyncSession) -> TallerOut:
    result = await db.execute(select(Taller).where(Taller.id_taller == id_taller))
    taller = result.scalar_one_or_none()
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(taller, field, value)

    await db.commit()
    await db.refresh(taller)
    return taller


async def cambiar_estado_taller(
    id_taller: int,
    data: TallerEstadoUpdate,
    db: AsyncSession,
) -> TallerOut:
    result = await db.execute(select(Taller).where(Taller.id_taller == id_taller))
    taller = result.scalar_one_or_none()
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado")

    taller.estado_registro = data.estado_registro
    await db.commit()
    await db.refresh(taller)
    return taller


async def obtener_metricas_taller(id_usuario: int, db: AsyncSession) -> dict:
    """Métricas del propio taller: solicitudes, servicios, ingresos y comisiones."""
    t_res = await db.execute(select(Taller).where(Taller.id_usuario == id_usuario))
    taller = t_res.scalar_one_or_none()
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado para este usuario")

    async def count_inc(estados: list[str]) -> int:
        r = await db.execute(
            select(func.count()).where(
                Incidente.id_taller == taller.id_taller,
                Incidente.estado.in_(estados)
            ).select_from(Incidente)
        )
        return r.scalar_one()

    total_recibidos    = await count_inc(["EN_PROCESO", "RESUELTO", "PAGADO", "CANCELADO"])
    en_proceso         = await count_inc(["EN_PROCESO"])
    completados        = await count_inc(["RESUELTO", "PAGADO"])
    cancelados         = await count_inc(["CANCELADO"])

    # Pagos completados relacionados con este taller
    sub_inc = select(Incidente.id_incidente).where(Incidente.id_taller == taller.id_taller)
    r_ing = await db.execute(
        select(func.sum(Pago.monto_taller), func.sum(Pago.comision_plataforma), func.count())
        .where(Pago.id_incidente.in_(sub_inc), Pago.estado == "COMPLETADO")
    )
    row = r_ing.one()
    ingresos_taller     = Decimal(str(row[0] or 0))
    comisiones_pagadas  = Decimal(str(row[1] or 0))
    pagos_completados   = row[2] or 0

    return {
        "id_taller":          taller.id_taller,
        "razon_social":       taller.razon_social,
        "estado_registro":    taller.estado_registro,
        "solicitudes_recibidas": total_recibidos,
        "en_proceso":         en_proceso,
        "completados":        completados,
        "cancelados":         cancelados,
        "pagos_completados":  pagos_completados,
        "ingresos_taller":    float(ingresos_taller),
        "comisiones_pagadas": float(comisiones_pagadas),
    }


async def obtener_pagos_taller(id_usuario: int, db: AsyncSession) -> list[dict]:
    """Lista los pagos relacionados con incidentes asignados a este taller.
    Útil para que el TALLER vea su impacto económico (sin tocar el módulo de pagos del cliente)."""
    t_res = await db.execute(select(Taller).where(Taller.id_usuario == id_usuario))
    taller = t_res.scalar_one_or_none()
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado para este usuario")

    sub_inc = select(Incidente.id_incidente).where(Incidente.id_taller == taller.id_taller)
    r_pagos = await db.execute(
        select(Pago, Incidente)
        .join(Incidente, Pago.id_incidente == Incidente.id_incidente)
        .where(Pago.id_incidente.in_(sub_inc))
        .order_by(Pago.created_at.desc())
    )
    items: list[dict] = []
    for pago, inc in r_pagos.all():
        items.append({
            "id_pago":             pago.id_pago,
            "id_incidente":        pago.id_incidente,
            "estado":              pago.estado,
            "metodo_pago":         pago.metodo_pago,
            "monto_total":         float(pago.monto_total),
            "monto_taller":        float(pago.monto_taller),
            "comision_plataforma": float(pago.comision_plataforma),
            "referencia":          pago.referencia,
            "created_at":          pago.created_at.isoformat(),
            "incidente_clasificacion": inc.clasificacion_ia,
            "incidente_estado":    inc.estado,
            "incidente_descripcion": inc.descripcion[:80] if inc.descripcion else "",
        })
    return items
