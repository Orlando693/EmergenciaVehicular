import logging
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.administracion.usuarios.model import Cliente, Usuario
from app.asignacion_atencion.notificaciones import service as notificacion_service
from app.bitacora_reportes.bitacora.model import Bitacora
from app.gestion_comercial_servicio.procesar_pago_pasarela.gateway_client import (
    DatosPago,
    GatewayRespuesta,
    ESTADO_APROBADO,
    ESTADO_RECHAZADO,
    ESTADO_PENDIENTE,
    ESTADO_ERROR_CONEXION,
    procesar_pago,
)
from app.gestion_comercial_servicio.procesar_pago_pasarela.model import PagoGatewayTransaccion
from app.gestion_comercial_servicio.procesar_pago_pasarela.schemas import (
    ConfirmarWebhookRequest,
    InfoPagoOut,
    ProcesarPagoRequest,
    ResultadoPagoOut,
)
from app.gestion_incidentes.incidentes.model import Incidente, IncidenteHistorial
from app.gestion_operativa_atencion.cotizaciones.model import CotizacionReparacion
from app.gestion_servicios.pagos.model import Pago
from app.gestion_servicios.pagos.service import calcular_monto, COMISION_PCT
from app.operaciones.talleres.model import Taller

logger = logging.getLogger(__name__)

# Incidente debe estar en uno de estos estados para poder pagar
_ESTADOS_PAGABLES = {"RESUELTO", "EN_PROCESO", "PAGADO"}


# ── Helpers privados ──────────────────────────────────────────────────────────

async def _get_cliente(db: AsyncSession, usuario: Usuario) -> Cliente:
    result = await db.execute(
        select(Cliente).where(
            Cliente.id_usuario == usuario.id_usuario,
            Cliente.id_tenant == usuario.id_tenant,
        )
    )
    cliente = result.scalar_one_or_none()
    if not cliente:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Perfil de cliente no encontrado")
    return cliente


async def _get_incidente(db: AsyncSession, id_incidente: int, id_cliente: int, id_tenant: int) -> Incidente:
    result = await db.execute(
        select(Incidente).where(
            Incidente.id_incidente == id_incidente,
            Incidente.id_cliente == id_cliente,
            Incidente.id_tenant == id_tenant,
        )
    )
    incidente = result.scalar_one_or_none()
    if not incidente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Servicio no encontrado")
    return incidente


async def _get_cotizacion_aceptada(
    db: AsyncSession, id_incidente: int, id_tenant: int
) -> CotizacionReparacion | None:
    result = await db.execute(
        select(CotizacionReparacion).where(
            CotizacionReparacion.id_incidente == id_incidente,
            CotizacionReparacion.id_tenant == id_tenant,
            CotizacionReparacion.estado == "ACEPTADA",
        )
    )
    return result.scalar_one_or_none()


def _calcular_montos(cotizacion: CotizacionReparacion | None, incidente: Incidente) -> tuple[Decimal, Decimal, Decimal]:
    """Devuelve (monto_total, monto_taller, comision)."""
    if cotizacion and cotizacion.precio_estimado:
        monto_total = cotizacion.precio_estimado
    else:
        monto_total = calcular_monto(incidente.clasificacion_ia)
    comision = (monto_total * COMISION_PCT).quantize(Decimal("0.01"))
    monto_taller = (monto_total - comision).quantize(Decimal("0.01"))
    return monto_total, monto_taller, comision


async def _contar_intentos(db: AsyncSession, id_pago: int) -> int:
    result = await db.execute(
        select(PagoGatewayTransaccion).where(
            PagoGatewayTransaccion.id_pago == id_pago
        ).order_by(PagoGatewayTransaccion.intento_numero.desc())
    )
    transacciones = result.scalars().all()
    return len(transacciones)


async def _registrar_bitacora(
    db: AsyncSession,
    usuario: Usuario,
    id_incidente: int,
    accion: str,
) -> None:
    db.add(Bitacora(
        id_tenant=usuario.id_tenant,
        modulo="CU23 Procesar pago mediante pasarela externa",
        accion=accion,
        rol="CLIENTE",
        usuario_email=usuario.email,
        id_usuario=usuario.id_usuario,
    ))


# ── Casos de uso públicos ─────────────────────────────────────────────────────

async def obtener_info_pago(
    db: AsyncSession,
    id_incidente: int,
    usuario: Usuario,
) -> InfoPagoOut:
    """
    Pasos 2-3 del flujo: muestra el monto total del servicio y el estado
    de pago actual para que el cliente decida iniciar la transacción.
    """
    cliente = await _get_cliente(db, usuario)
    incidente = await _get_incidente(db, id_incidente, cliente.id_cliente, usuario.id_tenant)
    cotizacion = await _get_cotizacion_aceptada(db, id_incidente, usuario.id_tenant)

    if incidente.estado not in _ESTADOS_PAGABLES and not cotizacion:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "El servicio no está disponible para pago. Debe existir una cotización "
                "aceptada o el servicio debe estar en estado RESUELTO o EN_PROCESO."
            ),
        )

    monto_total, monto_taller, comision = _calcular_montos(cotizacion, incidente)

    pago_result = await db.execute(
        select(Pago).where(Pago.id_incidente == id_incidente, Pago.id_tenant == usuario.id_tenant)
    )
    pago = pago_result.scalar_one_or_none()

    return InfoPagoOut(
        id_incidente=id_incidente,
        estado_incidente=incidente.estado,
        monto_total=monto_total,
        monto_taller=monto_taller,
        comision_plataforma=comision,
        cotizacion_aceptada_id=cotizacion.id_cotizacion if cotizacion else None,
        precio_cotizacion=cotizacion.precio_estimado if cotizacion else None,
        pago_estado=pago.estado if pago else None,
        pago_referencia=pago.referencia if pago else None,
    )


async def procesar_pago_gateway(
    db: AsyncSession,
    id_incidente: int,
    payload: ProcesarPagoRequest,
    usuario: Usuario,
) -> ResultadoPagoOut:
    """
    Pasos 4-13 del flujo: el cliente inicia el pago mediante la pasarela.

    1. Valida precondiciones (incidente asignado, monto correcto, no pagado ya).
    2. Crea/actualiza el registro Pago.
    3. Llama a la pasarela externa (gateway_client).
    4. Registra el intento en PagoGatewayTransaccion.
    5. Actualiza el estado del Pago y del Incidente según la respuesta.
    6. Notifica al cliente y al taller.
    7. Registra en bitácora.
    """
    cliente = await _get_cliente(db, usuario)
    incidente = await _get_incidente(db, id_incidente, cliente.id_cliente, usuario.id_tenant)
    cotizacion = await _get_cotizacion_aceptada(db, id_incidente, usuario.id_tenant)

    # Validar precondición: debe poder pagarse
    if incidente.estado not in _ESTADOS_PAGABLES and not cotizacion:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "No se puede procesar el pago. Requiere servicio en estado RESUELTO o "
                "EN_PROCESO, o una cotización aceptada con precio definido."
            ),
        )

    monto_total, monto_taller, comision = _calcular_montos(cotizacion, incidente)

    # Verificar pago existente
    pago_result = await db.execute(
        select(Pago).where(Pago.id_incidente == id_incidente, Pago.id_tenant == usuario.id_tenant)
    )
    pago = pago_result.scalar_one_or_none()

    # Paso 9: validar que el monto coincida si ya existe un pago
    if pago and pago.estado == "COMPLETADO":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este servicio ya fue pagado.",
        )
    if pago and pago.monto_total != monto_total:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"El monto del pago registrado (${pago.monto_total}) no coincide con "
                f"el monto actual del servicio (${monto_total}). Verifica la información."
            ),
        )

    # Crear registro Pago si no existe
    if not pago:
        pago = Pago(
            id_tenant=usuario.id_tenant,
            id_incidente=id_incidente,
            id_cliente=cliente.id_cliente,
            monto_total=monto_total,
            monto_taller=monto_taller,
            comision_plataforma=comision,
            metodo_pago=payload.metodo_pago.upper(),
            estado="PENDIENTE",
        )
        db.add(pago)
        await db.flush()  # obtiene id_pago sin commit

    intento_numero = await _contar_intentos(db, pago.id_pago) + 1

    # Paso 7-8: llamar a la pasarela externa
    datos_gateway = DatosPago(
        metodo_pago=payload.metodo_pago,
        monto=monto_total,
        numero_tarjeta=payload.numero_tarjeta,
        nombre_titular=payload.nombre_titular,
        vencimiento=payload.vencimiento,
        cvv=payload.cvv,
    )
    try:
        respuesta: GatewayRespuesta = await procesar_pago(datos_gateway, gateway=payload.gateway)
    except Exception as exc:
        logger.warning("[CU23] Error de conexión con la pasarela: %s", exc)
        respuesta = GatewayRespuesta(
            estado=ESTADO_ERROR_CONEXION,
            referencia="",
            codigo="TIMEOUT",
            mensaje=f"Error de conexión con la pasarela. Conservando pago sin confirmar. Detalle: {exc}",
        )

    # Registrar intento de transacción (paso 10)
    transaccion = PagoGatewayTransaccion(
        id_tenant=usuario.id_tenant,
        id_pago=pago.id_pago,
        gateway_nombre=payload.gateway,
        metodo_pago=payload.metodo_pago.upper(),
        monto=monto_total,
        intento_numero=intento_numero,
        gateway_referencia=respuesta.referencia or None,
        gateway_codigo=respuesta.codigo,
        gateway_mensaje=respuesta.mensaje,
        estado=respuesta.estado,
    )
    db.add(transaccion)

    # Actualizar estado del pago según respuesta del gateway
    estado_anterior_incidente = incidente.estado
    if respuesta.estado == ESTADO_APROBADO:
        pago.estado = "COMPLETADO"
        pago.referencia = respuesta.referencia
        pago.descripcion_error = None
        pago.metodo_pago = payload.metodo_pago.upper()
        incidente.estado = "PAGADO"
        db.add(IncidenteHistorial(
            id_tenant=usuario.id_tenant,
            id_incidente=id_incidente,
            estado_anterior=estado_anterior_incidente,
            estado_nuevo="PAGADO",
            observacion=(
                f"Pago aprobado por pasarela '{payload.gateway}'. "
                f"Método: {payload.metodo_pago.upper()}. Ref: {respuesta.referencia}. "
                f"Monto: ${monto_total:.2f}."
            ),
        ))
    elif respuesta.estado == ESTADO_RECHAZADO:
        pago.estado = "FALLIDO"
        pago.descripcion_error = respuesta.mensaje
        pago.metodo_pago = payload.metodo_pago.upper()
        db.add(IncidenteHistorial(
            id_tenant=usuario.id_tenant,
            id_incidente=id_incidente,
            estado_anterior=estado_anterior_incidente,
            estado_nuevo=estado_anterior_incidente,
            observacion=f"Intento de pago RECHAZADO por pasarela. Motivo: {respuesta.mensaje}.",
        ))
    elif respuesta.estado == ESTADO_PENDIENTE:
        pago.estado = "PENDIENTE"
        pago.referencia = respuesta.referencia
        pago.metodo_pago = payload.metodo_pago.upper()
    else:  # ERROR_CONEXION
        pago.estado = "PENDIENTE"
        pago.descripcion_error = respuesta.mensaje

    # Paso 13: bitácora
    await _registrar_bitacora(
        db, usuario, id_incidente,
        f"Intento #{intento_numero} de pago vía '{payload.gateway}' — estado: {respuesta.estado}. "
        f"Ref: {respuesta.referencia or 'N/A'}. Monto: ${monto_total:.2f}.",
    )

    await db.commit()
    await db.refresh(pago)
    await db.refresh(transaccion)

    # Paso 12: notificar al cliente y al taller
    await _notificar_resultado(db, incidente, pago, monto_total, monto_taller, comision, usuario, respuesta)

    return _construir_resultado(pago, incidente, transaccion, respuesta)


async def confirmar_webhook(
    db: AsyncSession,
    payload: ConfirmarWebhookRequest,
) -> ResultadoPagoOut:
    """
    Endpoint llamado por la pasarela para confirmar transacciones PENDIENTES.
    Actualiza el Pago y el Incidente según el estado final reportado.
    """
    # Buscar la transacción por referencia del gateway
    tx_result = await db.execute(
        select(PagoGatewayTransaccion)
        .where(PagoGatewayTransaccion.gateway_referencia == payload.gateway_referencia)
        .options(selectinload(PagoGatewayTransaccion.pago))
    )
    transaccion = tx_result.scalar_one_or_none()
    if not transaccion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró transacción con referencia '{payload.gateway_referencia}'",
        )

    pago = transaccion.pago
    if pago.estado == "COMPLETADO":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El pago ya fue confirmado anteriormente.",
        )

    incidente_result = await db.execute(
        select(Incidente).where(Incidente.id_incidente == pago.id_incidente)
    )
    incidente = incidente_result.scalar_one()

    # Actualizar con el estado final del gateway
    transaccion.estado = payload.estado
    if payload.codigo:
        transaccion.gateway_codigo = payload.codigo
    if payload.mensaje:
        transaccion.gateway_mensaje = payload.mensaje

    estado_anterior = incidente.estado
    if payload.estado == ESTADO_APROBADO:
        pago.estado = "COMPLETADO"
        pago.referencia = payload.gateway_referencia
        pago.descripcion_error = None
        incidente.estado = "PAGADO"
        db.add(IncidenteHistorial(
            id_tenant=pago.id_tenant,
            id_incidente=pago.id_incidente,
            estado_anterior=estado_anterior,
            estado_nuevo="PAGADO",
            observacion=f"Pago confirmado vía webhook. Ref: {payload.gateway_referencia}. Monto: ${pago.monto_total:.2f}.",
        ))
    elif payload.estado == ESTADO_RECHAZADO:
        pago.estado = "FALLIDO"
        pago.descripcion_error = payload.mensaje or "Rechazado por la pasarela"

    await db.commit()
    await db.refresh(pago)
    await db.refresh(transaccion)

    return _construir_resultado(pago, incidente, transaccion, None)


async def listar_transacciones(
    db: AsyncSession,
    id_incidente: int,
    usuario: Usuario,
) -> list[PagoGatewayTransaccion]:
    """Historial de intentos de pago del incidente del cliente."""
    cliente = await _get_cliente(db, usuario)
    incidente = await _get_incidente(db, id_incidente, cliente.id_cliente, usuario.id_tenant)

    pago_result = await db.execute(
        select(Pago).where(Pago.id_incidente == incidente.id_incidente, Pago.id_tenant == usuario.id_tenant)
    )
    pago = pago_result.scalar_one_or_none()
    if not pago:
        return []

    tx_result = await db.execute(
        select(PagoGatewayTransaccion)
        .where(PagoGatewayTransaccion.id_pago == pago.id_pago)
        .order_by(PagoGatewayTransaccion.intento_numero.asc())
    )
    return tx_result.scalars().all()


# ── Helpers internos ──────────────────────────────────────────────────────────

async def _notificar_resultado(
    db: AsyncSession,
    incidente: Incidente,
    pago: Pago,
    monto_total: Decimal,
    monto_taller: Decimal,
    comision: Decimal,
    usuario: Usuario,
    respuesta: GatewayRespuesta,
) -> None:
    try:
        if respuesta.estado == ESTADO_APROBADO:
            titulo_cliente = f"Pago confirmado — Servicio #{incidente.id_incidente}"
            msg_cliente = (
                f"Tu pago de ${monto_total:.2f} fue aprobado. "
                f"Referencia: {respuesta.referencia}. Gracias por usar la plataforma."
            )
        elif respuesta.estado == ESTADO_RECHAZADO:
            titulo_cliente = f"Pago rechazado — Servicio #{incidente.id_incidente}"
            msg_cliente = f"Tu pago fue rechazado. {respuesta.mensaje} Intenta nuevamente."
        else:
            titulo_cliente = f"Pago pendiente — Servicio #{incidente.id_incidente}"
            msg_cliente = (
                f"Tu pago de ${monto_total:.2f} está siendo procesado. "
                f"Referencia: {respuesta.referencia or 'en proceso'}. Te notificaremos la confirmación."
            )

        await notificacion_service.crear_notificacion(
            db=db,
            id_usuario=usuario.id_usuario,
            titulo=titulo_cliente,
            mensaje=msg_cliente,
            tipo="PAGO_GATEWAY",
            id_incidente=incidente.id_incidente,
            id_tenant=usuario.id_tenant,
        )
    except Exception as exc:
        logger.warning("[CU23] No se pudo notificar al cliente: %s", exc)

    if respuesta.estado == ESTADO_APROBADO and incidente.id_taller:
        try:
            tr = await db.execute(
                select(Taller).where(Taller.id_taller == incidente.id_taller)
            )
            taller = tr.scalar_one_or_none()
            if taller:
                await notificacion_service.crear_notificacion(
                    db=db,
                    id_usuario=taller.id_usuario,
                    titulo=f"Pago recibido — Servicio #{incidente.id_incidente}",
                    mensaje=(
                        f"El cliente pagó ${monto_total:.2f}. "
                        f"Tu parte: ${monto_taller:.2f} · Comisión: ${comision:.2f}. "
                        f"Ref: {respuesta.referencia}."
                    ),
                    tipo="PAGO_RECIBIDO",
                    id_incidente=incidente.id_incidente,
                    id_tenant=usuario.id_tenant,
                )
        except Exception as exc:
            logger.warning("[CU23] No se pudo notificar al taller: %s", exc)


def _construir_resultado(
    pago: Pago,
    incidente: Incidente,
    transaccion: PagoGatewayTransaccion,
    respuesta: GatewayRespuesta | None,
) -> ResultadoPagoOut:
    mensajes = {
        "COMPLETADO": "Pago aprobado. El servicio ha quedado marcado como pagado.",
        "FALLIDO":    "Pago rechazado. Revisa los datos e inténtalo de nuevo.",
        "PENDIENTE":  "Pago en proceso. Recibirás una notificación con la confirmación.",
    }
    return ResultadoPagoOut(
        id_pago=pago.id_pago,
        id_incidente=pago.id_incidente,
        estado_pago=pago.estado,
        referencia=pago.referencia,
        monto_total=pago.monto_total,
        estado_incidente=incidente.estado,
        transaccion=transaccion,
        mensaje=mensajes.get(pago.estado, "Estado de pago actualizado."),
    )
