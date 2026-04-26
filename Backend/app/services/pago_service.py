import random
import string
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incidente import Incidente, IncidenteHistorial
from app.models.cliente import Cliente
from app.models.pago import Pago
from app.models.taller import Taller
from app.services import notificacion_service
import logging

logger = logging.getLogger(__name__)

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


async def obtener_info_pago(
    id_incidente: int,
    id_usuario: int,
    es_admin: bool,
    es_taller: bool,
    es_cliente: bool,
    db: AsyncSession,
) -> dict:
    """A2 - Devuelve la misma info de costo+pago para CLIENTE dueño, TALLER asignado o ADMIN.
    No exige que el incidente esté en RESUELTO; sirve también para mostrar el pago ya existente."""
    r = await db.execute(select(Incidente).where(Incidente.id_incidente == id_incidente))
    incidente = r.scalar_one_or_none()
    if not incidente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incidente no encontrado")

    if es_admin:
        pass
    elif es_taller:
        tr = await db.execute(select(Taller).where(Taller.id_usuario == id_usuario))
        taller = tr.scalar_one_or_none()
        if not taller or incidente.id_taller != taller.id_taller:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes acceso a este servicio")
    elif es_cliente:
        cr = await db.execute(select(Cliente).where(Cliente.id_usuario == id_usuario))
        cliente = cr.scalar_one_or_none()
        if not cliente or incidente.id_cliente != cliente.id_cliente:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes acceso a este incidente")
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")

    monto = calcular_monto(incidente.clasificacion_ia)
    comision = (monto * COMISION_PCT).quantize(Decimal("0.01"))
    al_taller = (monto - comision).quantize(Decimal("0.01"))

    pr = await db.execute(select(Pago).where(Pago.id_incidente == id_incidente))
    pago = pr.scalar_one_or_none()

    return {
        "id_incidente":        id_incidente,
        "clasificacion_ia":    incidente.clasificacion_ia,
        "estado_incidente":    incidente.estado,
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
        hist = IncidenteHistorial(
            id_incidente=id_incidente,
            estado_anterior="RESUELTO",
            estado_nuevo="PAGADO",
            observacion=f"Pago completado. Método: {metodo_upper}. Referencia: {referencia}. Monto: ${monto:.2f}."
        )
        db.add(hist)
        await db.commit()

        # Notificar al cliente
        try:
            await notificacion_service.crear_notificacion(
                db=db,
                id_usuario=id_usuario,
                titulo=f"Pago confirmado — Incidente #{id_incidente}",
                mensaje=f"Tu pago de ${monto:.2f} fue procesado exitosamente. Referencia: {referencia}.",
                tipo="PAGO_REALIZADO",
                id_incidente=id_incidente,
            )
        except Exception as exc:
            logger.warning(f"[Pago] No se pudo notificar al cliente: {exc}")

        # Notificar al taller asignado (A1 - sincronización pago → taller)
        try:
            if incidente.id_taller is not None:
                tr = await db.execute(select(Taller).where(Taller.id_taller == incidente.id_taller))
                taller = tr.scalar_one_or_none()
                if taller:
                    await notificacion_service.crear_notificacion(
                        db=db,
                        id_usuario=taller.id_usuario,
                        titulo=f"Pago recibido — Incidente #{id_incidente}",
                        mensaje=(
                            f"El cliente pagó ${monto:.2f}. "
                            f"Tu parte (90%): ${al_taller:.2f} · "
                            f"Comisión (10%): ${comision:.2f}. Ref: {referencia}."
                        ),
                        tipo="PAGO_RECIBIDO",
                        id_incidente=id_incidente,
                    )
        except Exception as exc:
            logger.warning(f"[Pago] No se pudo notificar al taller: {exc}")

    elif estado == "FALLIDO":
        # También dejar trazabilidad del intento fallido
        try:
            hist_fail = IncidenteHistorial(
                id_incidente=id_incidente,
                estado_anterior=incidente.estado,
                estado_nuevo=incidente.estado,
                observacion=f"Intento de pago FALLIDO. Método: {metodo_upper}. Motivo: {error_msg or 'desconocido'}.",
            )
            db.add(hist_fail)
            await db.commit()
        except Exception:
            await db.rollback()

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
