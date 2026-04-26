import random
import string
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incidente import Incidente
from app.models.cliente import Cliente
from app.models.pago import Pago
from app.services import notificacion_service

COMISION_PCT = Decimal("0.10")

# ── Tarifa por tipo de incidente ──────────────────────────────────────────────
_TARIFAS = [
    (["COLISION", "ACCIDENTE", "CHOQUE", "IMPACTO"],       Decimal("450.00")),
    (["MOTOR", "MECANICA", "MECANICO", "FALLA", "AVERIA"], Decimal("280.00")),
    (["LLANTA", "PINCHAZO", "NEUMATICO", "RUEDA"],         Decimal("90.00")),
    (["BATERIA", "ARRANQUE", "ELECTRICA", "ELECTRICO"],    Decimal("70.00")),
    (["GRUA", "REMOLQUE", "ARRASTRE"],                     Decimal("200.00")),
]
_TARIFA_DEFAULT = Decimal("180.00")


def calcular_monto(clasificacion: str | None) -> Decimal:
    if not clasificacion:
        return _TARIFA_DEFAULT
    upper = clasificacion.upper()
    for keywords, monto in _TARIFAS:
        if any(k in upper for k in keywords):
            return monto
    return _TARIFA_DEFAULT


def _generar_referencia() -> str:
    return "TXN-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=10))


# ── Helpers de autorización ───────────────────────────────────────────────────

async def _obtener_incidente_y_cliente(
    id_incidente: int, id_usuario: int, db: AsyncSession
) -> tuple[Incidente, Cliente]:
    r = await db.execute(select(Incidente).where(Incidente.id_incidente == id_incidente))
    incidente = r.scalar_one_or_none()
    if not incidente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incidente no encontrado")

    cr = await db.execute(select(Cliente).where(Cliente.id_usuario == id_usuario))
    cliente = cr.scalar_one_or_none()
    if not cliente:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo clientes pueden realizar pagos")

    if incidente.id_cliente != cliente.id_cliente:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes acceso a este incidente")

    if incidente.estado not in ("RESUELTO",):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El servicio debe estar finalizado (RESUELTO) para poder pagar.",
        )

    return incidente, cliente


# ── Servicio principal ────────────────────────────────────────────────────────

async def obtener_costo(id_incidente: int, id_usuario: int, db: AsyncSession) -> dict:
    incidente, cliente = await _obtener_incidente_y_cliente(id_incidente, id_usuario, db)

    monto = calcular_monto(incidente.clasificacion_ia)
    comision = (monto * COMISION_PCT).quantize(Decimal("0.01"))
    al_taller = (monto - comision).quantize(Decimal("0.01"))

    # ¿Ya existe un pago?
    pr = await db.execute(select(Pago).where(Pago.id_incidente == id_incidente))
    pago = pr.scalar_one_or_none()

    return {
        "id_incidente":        id_incidente,
        "clasificacion_ia":    incidente.clasificacion_ia,
        "monto_total":         monto,
        "monto_taller":        al_taller,
        "comision_plataforma": comision,
        "pago_existente":      pago,
    }


async def iniciar_pago(
    id_incidente: int,
    id_usuario:   int,
    metodo_pago:  str,
    numero_tarjeta: str | None,
    db: AsyncSession,
) -> Pago:
    incidente, cliente = await _obtener_incidente_y_cliente(id_incidente, id_usuario, db)

    # Solo un pago por incidente
    pr = await db.execute(select(Pago).where(Pago.id_incidente == id_incidente))
    pago_existente = pr.scalar_one_or_none()
    if pago_existente and pago_existente.estado == "COMPLETADO":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Este servicio ya fue pagado.")

    monto = calcular_monto(incidente.clasificacion_ia)
    comision = (monto * COMISION_PCT).quantize(Decimal("0.01"))
    al_taller = (monto - comision).quantize(Decimal("0.01"))

    # ── Simulación del procesador de pagos ────────────────────────
    metodo_upper = metodo_pago.upper()
    if metodo_upper in ("EFECTIVO", "TRANSFERENCIA"):
        aprobado = True
        error_msg = None
    else:
        # Tarjeta: falla si termina en "0000" (modo demo) o es inválida
        ultimos = (numero_tarjeta or "").replace(" ", "")[-4:]
        aprobado = ultimos != "0000" and len(ultimos) == 4
        error_msg = "Tarjeta declinada. Verifique los datos o intente con otra tarjeta." if not aprobado else None

    estado = "COMPLETADO" if aprobado else "FALLIDO"
    referencia = _generar_referencia() if aprobado else None

    if pago_existente:
        # Re-intentar pago fallido
        pago_existente.metodo_pago       = metodo_upper
        pago_existente.estado            = estado
        pago_existente.referencia        = referencia
        pago_existente.descripcion_error = error_msg
        await db.commit()
        await db.refresh(pago_existente)
        pago = pago_existente
    else:
        pago = Pago(
            id_incidente=id_incidente,
            id_cliente=cliente.id_cliente,
            monto_total=monto,
            monto_taller=al_taller,
            comision_plataforma=comision,
            metodo_pago=metodo_upper,
            estado=estado,
            referencia=referencia,
            descripcion_error=error_msg,
        )
        db.add(pago)
        await db.commit()
        await db.refresh(pago)

    # Si el pago fue exitoso, marcar incidente como PAGADO
    if aprobado:
        incidente.estado = "PAGADO"
        db.add(incidente)
        await db.commit()

        # Notificar al cliente
        try:
            await notificacion_service.crear_notificacion(
                db=db,
                id_usuario=id_usuario,
                titulo=f"Pago confirmado — Incidente #{id_incidente}",
                mensaje=f"Tu pago de ${monto:.2f} fue procesado exitosamente. Referencia: {referencia}.",
                tipo="INFO",
                id_incidente=id_incidente,
            )
        except Exception:
            pass

    return pago


async def listar_pagos_cliente(id_usuario: int, db: AsyncSession, skip: int = 0, limit: int = 20) -> dict:
    cr = await db.execute(select(Cliente).where(Cliente.id_usuario == id_usuario))
    cliente = cr.scalar_one_or_none()
    if not cliente:
        return {"items": [], "total": 0}

    total_r = await db.execute(
        select(func.count()).where(Pago.id_cliente == cliente.id_cliente).select_from(Pago)
    )
    total = total_r.scalar_one()

    items_r = await db.execute(
        select(Pago)
        .where(Pago.id_cliente == cliente.id_cliente)
        .order_by(Pago.created_at.desc())
        .offset(skip).limit(limit)
    )
    return {"items": items_r.scalars().all(), "total": total}


async def listar_todos_pagos(db: AsyncSession, skip: int = 0, limit: int = 20) -> dict:
    total_r = await db.execute(select(func.count()).select_from(Pago))
    total = total_r.scalar_one()
    items_r = await db.execute(
        select(Pago).order_by(Pago.created_at.desc()).offset(skip).limit(limit)
    )
    return {"items": items_r.scalars().all(), "total": total}
