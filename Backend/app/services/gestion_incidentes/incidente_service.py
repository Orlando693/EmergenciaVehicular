from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.incidente import Incidente, IncidenteHistorial
from app.models.cliente import Cliente
from app.models.taller import Taller
from app.models.vehiculo import Vehiculo
from app.models.pago import Pago
from app.schemas.incidente import IncidenteOut, IncidenteCreate, IncidenteHistorialOut, IncidenteEstadoUpdate
from app.services.asignacion_atencion import notificacion_service
import asyncio
import mimetypes
import os
import time
import logging
from google import genai
from google.genai import types as genai_types

logger = logging.getLogger(__name__)


def _resolve_upload_path(public_url: str | None) -> str | None:
    """Convierte una URL pública (/public/uploads/X.jpg) al path real en disco.

    Soporta tanto la convención por defecto (public/uploads) como un
    UPLOAD_DIR personalizado (ej. /data/uploads en Railway con Volume)."""
    if not public_url:
        return None
    prefix = settings.UPLOAD_URL_PREFIX.rstrip("/") + "/"
    if public_url.startswith(prefix):
        relative = public_url[len(prefix):]
        return os.path.join(settings.UPLOAD_DIR, relative)
    # Fallback: comportamiento histórico (URL relativa como "/public/uploads/X")
    return public_url.lstrip("/")


def _build_image_part(image_path: str):
    """Lee la imagen del disco y devuelve un Part inline para el nuevo SDK google.genai."""
    if not os.path.exists(image_path):
        logger.warning(f"Imagen no encontrada en disco: {image_path}")
        return None

    file_size = os.path.getsize(image_path)
    if file_size > 19 * 1024 * 1024:
        logger.warning(f"Imagen demasiado grande para inline ({file_size} bytes). Se omite.")
        return None

    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type or not mime_type.startswith("image/"):
        mime_type = "image/jpeg"

    with open(image_path, "rb") as f:
        data = f.read()

    return genai_types.Part.from_bytes(data=data, mime_type=mime_type)


def _upload_and_wait_audio(client: genai.Client, audio_path: str):
    """Sube el audio al File API de Gemini y espera hasta que este ACTIVE."""
    if not os.path.exists(audio_path):
        logger.warning(f"Audio no encontrado en disco: {audio_path}")
        return None

    try:
        audio_file = client.files.upload(file=audio_path)
        deadline = time.time() + 60
        while getattr(audio_file, 'state', None) and str(audio_file.state) in ("FileState.PROCESSING", "PROCESSING") and time.time() < deadline:
            time.sleep(2)
            audio_file = client.files.get(name=audio_file.name)

        state_str = str(getattr(audio_file, 'state', 'ACTIVE'))
        if "ACTIVE" in state_str:
            return audio_file

        logger.warning(f"Audio no quedo ACTIVE a tiempo. Estado: {state_str}")
        return None
    except Exception as exc:
        logger.warning(f"No se pudo procesar el audio con File API: {exc}")
        return None


async def procesar_con_ia(descripcion: str, audio_url: str | None, imagen_url: str | None) -> dict:
    """
    Analisis multimodal real con Google Gemini 1.5 Flash (google-genai SDK).
    Procesa texto + imagen (inline bytes) + audio (File API).
    Si GEMINI_API_KEY no esta configurada devuelve analisis basico de texto.
    """
    api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")

    if not api_key:
        logger.warning("GEMINI_API_KEY no configurada. Usando analisis de texto basico.")
        clasificacion = "MECANICO"
        desc_lower = (descripcion or "").lower()
        if any(w in desc_lower for w in ("choque", "accidente", "colision", "golpe", "impacto", "atropello", "rozar")):
            clasificacion = "COLISION"
        elif any(w in desc_lower for w in ("neumatico", "llanta", "ponchado", "rueda", "pinchazo", "desinflad")):
            clasificacion = "NEUMATICOS"
        elif any(w in desc_lower for w in ("electrico", "bateria", "luz", "faro", "corto", "arranque", "no enciende", "no prende")):
            clasificacion = "ELECTRICO"

        recomendaciones = {
            "MECANICO":   "Recomendación inicial: detener el vehículo en un lugar seguro, no intentar continuar la marcha y solicitar asistencia mecánica para diagnóstico en sitio.",
            "COLISION":   "Recomendación inicial: priorizar la seguridad de los ocupantes, señalizar el área, tomar fotos del vehículo y solicitar asistencia para remolque y peritaje.",
            "NEUMATICOS": "Recomendación inicial: estacionar en una zona segura, evitar continuar la marcha con el neumático afectado y solicitar cambio o reparación de llanta.",
            "ELECTRICO":  "Recomendación inicial: apagar luces y accesorios, no intentar arranques repetidos y solicitar asistencia para revisión de batería y sistema eléctrico.",
        }
        reco = recomendaciones.get(clasificacion, "Recomendación inicial: solicitar asistencia técnica para evaluación en sitio.")

        fuentes = ["texto"]
        if audio_url:
            fuentes.append("audio")
        if imagen_url:
            fuentes.append("imagen")

        return {
            "clasificacion": clasificacion,
            "resumen": (
                f"Diagnóstico preliminar: posible incidente de tipo {clasificacion} "
                f"según el reporte del cliente ({', '.join(fuentes)}). {reco}"
            )
        }

    try:
        client = genai.Client(api_key=api_key)

        content_parts: list = []
        fuentes_analizadas: list[str] = ["texto"]

        # Imagen: se envia como inline bytes directamente
        if imagen_url:
            image_path = _resolve_upload_path(imagen_url)
            image_part = _build_image_part(image_path) if image_path else None
            if image_part:
                content_parts.append(image_part)
                fuentes_analizadas.append("imagen")

        # Audio: se sube al File API y se referencia
        if audio_url:
            audio_path = _resolve_upload_path(audio_url)
            audio_ref = await asyncio.to_thread(_upload_and_wait_audio, client, audio_path) if audio_path else None
            if audio_ref:
                content_parts.append(audio_ref)
                fuentes_analizadas.append("audio")

        medios_str = ", ".join(fuentes_analizadas)
        imagen_nota = "(Analiza tambien la imagen adjunta del vehiculo o accidente.)" if "imagen" in fuentes_analizadas else ""
        audio_nota = "(Analiza tambien el audio adjunto del cliente describiendo el problema.)" if "audio" in fuentes_analizadas else ""

        prompt = f"""Eres un experto en diagnostico de emergencias vehiculares.

El cliente reporta el siguiente problema con su vehiculo:
"{descripcion}"

Fuentes disponibles para analizar: {medios_str}
{imagen_nota}
{audio_nota}

Basandote en TODA la informacion disponible (texto, imagen y/o audio), realiza:
1. Clasifica el incidente en EXACTAMENTE UNO de estos tipos: MECANICO, COLISION, NEUMATICOS, ELECTRICO, OTRO
2. Redacta un resumen profesional de 2 oraciones con el problema detectado y las recomendaciones inmediatas.

Responde SOLAMENTE con este formato (exactamente 2 lineas, sin asteriscos ni texto adicional):
CLASIFICACION: <TIPO>
RESUMEN: <resumen profesional de 2 oraciones>"""

        content_parts.append(prompt)

        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-2.5-flash",
            contents=content_parts
        )

        clasificacion = "OTRO"
        resumen = "Analisis IA completado."

        for line in response.text.strip().splitlines():
            line = line.strip().replace("*", "")
            if line.upper().startswith("CLASIFICACION:"):
                clasificacion = line.split(":", 1)[1].strip().upper()
            elif line.upper().startswith("RESUMEN:"):
                resumen = line.split(":", 1)[1].strip()

        return {"clasificacion": clasificacion, "resumen": resumen}

    except Exception as exc:
        logger.error(f"Error invocando Gemini: {exc}")
        desc_lower = (descripcion or "").lower()
        clasificacion = "MECANICO"
        if any(w in desc_lower for w in ("choque", "accidente", "colision", "golpe", "impacto", "atropello")):
            clasificacion = "COLISION"
        elif any(w in desc_lower for w in ("neumatico", "llanta", "ponchado", "rueda", "pinchazo", "desinflad")):
            clasificacion = "NEUMATICOS"
        elif any(w in desc_lower for w in ("electrico", "bateria", "luz", "faro", "corto", "arranque", "no enciende", "no prende")):
            clasificacion = "ELECTRICO"
        return {
            "clasificacion": clasificacion,
            "resumen": (
                "No se pudo completar la consulta externa con Gemini en este momento, "
                f"pero se genero un diagnostico preliminar local de tipo {clasificacion}. "
                "Mantente en un lugar seguro, evita mover el vehiculo si hay riesgo y espera asistencia."
            )
        }


async def registrar_incidente_inteligente(data: IncidenteCreate, id_usuario: int, db: AsyncSession) -> IncidenteOut:
    cliente = await get_cliente_by_usuario_id(id_usuario, db)

    # 1. Validar vehiculo
    vehiculo_stmt = select(Vehiculo).where(
        Vehiculo.id_vehiculo == data.id_vehiculo,
        Vehiculo.id_cliente == cliente.id_cliente
    )
    veh_result = await db.execute(vehiculo_stmt)
    vehiculo = veh_result.scalar_one_or_none()

    if not vehiculo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El vehiculo no existe o no pertenece al cliente"
        )

    if not data.descripcion and not data.audio_url and not data.imagen_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe proveer al menos texto, audio o imagen para procesar el incidente"
        )

    # 2. Procesamiento IA real o fallback
    ia_result = await procesar_con_ia(data.descripcion, data.audio_url, data.imagen_url)

    # 3. Guardar Incidente
    nuevo_incidente = Incidente(
        id_cliente=cliente.id_cliente,
        id_vehiculo=vehiculo.id_vehiculo,
        descripcion=data.descripcion,
        audio_url=data.audio_url,
        imagen_url=data.imagen_url,
        ubicacion_lat=data.ubicacion_lat,
        ubicacion_lng=data.ubicacion_lng,
        direccion=data.direccion,
        estado="REPORTADO",
        clasificacion_ia=ia_result["clasificacion"],
        resumen_ia=ia_result["resumen"]
    )

    db.add(nuevo_incidente)
    await db.commit()
    await db.refresh(nuevo_incidente)

    # Historial: evento de creacion
    hist_creacion = IncidenteHistorial(
        id_incidente=nuevo_incidente.id_incidente,
        estado_anterior=None,
        estado_nuevo="REPORTADO",
        observacion=f"Incidente registrado. IA clasificó: {ia_result['clasificacion']}."
    )
    db.add(hist_creacion)
    await db.commit()

    # Notificar al cliente que su incidente fue registrado y analizado
    try:
        await notificacion_service.crear_notificacion(
            db=db,
            id_usuario=id_usuario,
            titulo=f"Incidente #{nuevo_incidente.id_incidente} registrado",
            mensaje=f"Tu reporte fue analizado por IA. Clasificacion: {ia_result['clasificacion']}. {ia_result['resumen'][:120]}",
            tipo="NUEVO_INCIDENTE",
            id_incidente=nuevo_incidente.id_incidente,
        )
    except Exception as exc:
        logger.warning(f"No se pudo crear notificacion de registro: {exc}")

    return await obtener_detalle_incidente(nuevo_incidente.id_incidente, id_usuario, es_admin=False, es_taller=False, db=db)


async def get_cliente_by_usuario_id(id_usuario: int, db: AsyncSession) -> Cliente:
    result = await db.execute(select(Cliente).where(Cliente.id_usuario == id_usuario))
    cliente = result.scalar_one_or_none()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado asociado a este usuario"
        )
    return cliente


async def consultar_historial_incidentes(id_usuario: int, es_admin: bool, es_taller: bool, db: AsyncSession) -> list[IncidenteOut]:
    stmt = select(Incidente).options(
        selectinload(Incidente.taller),
        selectinload(Incidente.vehiculo)
    ).order_by(Incidente.created_at.desc())

    if not es_admin:
        if es_taller:
            stmt_taller = select(Taller).where(Taller.id_usuario == id_usuario)
            res_taller = await db.execute(stmt_taller)
            taller = res_taller.scalar_one_or_none()
            id_taller = taller.id_taller if taller else -1
            stmt = stmt.where(Incidente.id_taller == id_taller)
        else:
            cliente = await get_cliente_by_usuario_id(id_usuario, db)
            stmt = stmt.where(Incidente.id_cliente == cliente.id_cliente)

    result = await db.execute(stmt)
    incidentes = result.scalars().all()

    response = []
    for inc in incidentes:
        inc_data = IncidenteOut.model_validate(inc)
        if inc.taller:
            inc_data.taller_nombre = inc.taller.razon_social
        if inc.vehiculo:
            inc_data.vehiculo_placa = inc.vehiculo.placa
            inc_data.vehiculo_marca = inc.vehiculo.marca
            inc_data.vehiculo_modelo = inc.vehiculo.modelo
        response.append(inc_data)

    return response


async def consultar_solicitudes_disponibles(db: AsyncSession) -> list[IncidenteOut]:
    stmt = select(Incidente).options(
        selectinload(Incidente.vehiculo)
    ).where(
        Incidente.estado == "REPORTADO",
        Incidente.id_taller.is_(None)
    ).order_by(Incidente.created_at.desc())

    result = await db.execute(stmt)
    incidentes = result.scalars().all()

    response = []
    for inc in incidentes:
        inc_data = IncidenteOut.model_validate(inc)
        if inc.vehiculo:
            inc_data.vehiculo_placa = inc.vehiculo.placa
            inc_data.vehiculo_marca = inc.vehiculo.marca
            inc_data.vehiculo_modelo = inc.vehiculo.modelo
        response.append(inc_data)

    return response


async def actualizar_estado_incidente(id_incidente: int, id_usuario: int, data: IncidenteEstadoUpdate, db: AsyncSession) -> IncidenteOut:
    stmt_taller = select(Taller).where(Taller.id_usuario == id_usuario)
    res_taller = await db.execute(stmt_taller)
    taller = res_taller.scalar_one_or_none()

    if not taller:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado o no es un taller valido")

    stmt = select(Incidente).where(
        Incidente.id_incidente == id_incidente,
        Incidente.id_taller == taller.id_taller
    )
    result = await db.execute(stmt)
    incidente = result.scalar_one_or_none()

    if not incidente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Servicio no encontrado o no asignado a este taller"
        )

    estado_viejo = incidente.estado
    if estado_viejo == data.estado:
        raise HTTPException(status_code=400, detail="El incidente ya se encuentra en este estado")

    incidente.estado = data.estado

    historial = IncidenteHistorial(
        id_incidente=incidente.id_incidente,
        estado_anterior=estado_viejo,
        estado_nuevo=data.estado,
        observacion=data.observacion
    )

    db.add(historial)
    db.add(incidente)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al actualizar el estado del servicio")

    # Notificar al cliente del cambio de estado
    try:
        cliente_r = await db.execute(select(Cliente).where(Cliente.id_cliente == incidente.id_cliente))
        cliente = cliente_r.scalar_one_or_none()
        if cliente:
            mensajes = {
                "EN_PROCESO": "Tu incidente esta siendo atendido por el taller asignado.",
                "RESUELTO":   "Tu incidente ha sido resuelto exitosamente. Gracias por usar nuestro servicio.",
                "CANCELADO":  "Tu incidente ha sido cancelado.",
            }
            msg = mensajes.get(data.estado, f"El estado de tu incidente cambio a {data.estado}.")
            await notificacion_service.crear_notificacion(
                db=db,
                id_usuario=cliente.id_usuario,
                titulo=f"Incidente #{incidente.id_incidente} — {data.estado}",
                mensaje=msg,
                tipo="ESTADO_CAMBIO",
                id_incidente=incidente.id_incidente,
            )
    except Exception as exc:
        logger.warning(f"No se pudo crear notificacion de cambio de estado: {exc}")

    return await obtener_detalle_incidente(id_incidente, 0, es_admin=True, es_taller=False, db=db)


async def consultar_historial_servicio(id_incidente: int, id_usuario: int, es_admin: bool, es_taller: bool, db: AsyncSession) -> list[IncidenteHistorialOut]:
    stmt = select(Incidente).where(Incidente.id_incidente == id_incidente)
    if not es_admin:
        if es_taller:
            stmt_taller = select(Taller).where(Taller.id_usuario == id_usuario)
            taller = (await db.execute(stmt_taller)).scalar_one_or_none()
            stmt = stmt.where(Incidente.id_taller == (taller.id_taller if taller else -1))
        else:
            cliente = await get_cliente_by_usuario_id(id_usuario, db)
            stmt = stmt.where(Incidente.id_cliente == cliente.id_cliente)

    res = await db.execute(stmt)
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incidente no accesible")

    historial_stmt = select(IncidenteHistorial).where(
        IncidenteHistorial.id_incidente == id_incidente
    ).order_by(IncidenteHistorial.created_at.desc())
    h_res = await db.execute(historial_stmt)
    return [IncidenteHistorialOut.model_validate(h) for h in h_res.scalars().all()]


async def obtener_detalle_solicitud(id_incidente: int, db: AsyncSession) -> IncidenteOut:
    stmt = select(Incidente).options(
        selectinload(Incidente.vehiculo)
    ).where(
        Incidente.id_incidente == id_incidente,
        Incidente.estado == "REPORTADO",
        Incidente.id_taller.is_(None)
    )

    result = await db.execute(stmt)
    incidente = result.scalar_one_or_none()

    if not incidente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitud no encontrada o ya no esta disponible"
        )

    inc_data = IncidenteOut.model_validate(incidente)
    if incidente.vehiculo:
        inc_data.vehiculo_placa = incidente.vehiculo.placa
        inc_data.vehiculo_marca = incidente.vehiculo.marca
        inc_data.vehiculo_modelo = incidente.vehiculo.modelo

    return inc_data


async def obtener_metricas_cliente(id_usuario: int, db: AsyncSession) -> dict:
    """Resumen de incidentes y pagos pendientes del cliente."""
    cliente = await get_cliente_by_usuario_id(id_usuario, db)

    async def count_state(estado: str) -> int:
        r = await db.execute(
            select(func.count()).where(
                Incidente.id_cliente == cliente.id_cliente,
                Incidente.estado == estado
            ).select_from(Incidente)
        )
        return r.scalar_one()

    r_total = await db.execute(
        select(func.count()).where(Incidente.id_cliente == cliente.id_cliente).select_from(Incidente)
    )
    total = r_total.scalar_one()
    reportados   = await count_state("REPORTADO")
    en_proceso   = await count_state("EN_PROCESO")
    resueltos    = await count_state("RESUELTO")
    pagados      = await count_state("PAGADO")
    cancelados   = await count_state("CANCELADO")

    r_gastado = await db.execute(
        select(func.sum(Pago.monto_total))
        .where(Pago.id_cliente == cliente.id_cliente, Pago.estado == "COMPLETADO")
    )
    gastado = float(r_gastado.scalar_one() or 0)

    return {
        "total_incidentes":    total,
        "reportados":          reportados,
        "en_proceso":          en_proceso,
        "pendientes_de_pago":  resueltos,
        "pagados":             pagados,
        "cancelados":          cancelados,
        "total_gastado":       gastado,
    }


async def obtener_detalle_incidente(id_incidente: int, id_usuario: int, es_admin: bool, es_taller: bool, db: AsyncSession) -> IncidenteOut:
    stmt = select(Incidente).options(
        selectinload(Incidente.vehiculo),
        selectinload(Incidente.taller)
    ).where(Incidente.id_incidente == id_incidente)

    result = await db.execute(stmt)
    incidente = result.scalar_one_or_none()

    if not incidente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incidente no encontrado"
        )

    if not es_admin:
        if es_taller:
            taller_stmt = select(Taller).where(Taller.id_usuario == id_usuario)
            taller_res = await db.execute(taller_stmt)
            taller = taller_res.scalar_one_or_none()
            if not taller or incidente.id_taller != taller.id_taller:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado para ver este servicio.")
        else:
            cliente_stmt = select(Cliente).where(Cliente.id_usuario == id_usuario)
            cliente_res = await db.execute(cliente_stmt)
            cliente = cliente_res.scalar_one_or_none()
            if not cliente or incidente.id_cliente != cliente.id_cliente:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado para ver este incidente.")

    inc_data = IncidenteOut.model_validate(incidente)
    if incidente.vehiculo:
        inc_data.vehiculo_placa = incidente.vehiculo.placa
        inc_data.vehiculo_marca = incidente.vehiculo.marca
        inc_data.vehiculo_modelo = incidente.vehiculo.modelo
    if incidente.taller:
        inc_data.taller_nombre = incidente.taller.razon_social

    return inc_data
