import asyncio
import logging
import os
import time
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.gestion_incidentes.incidentes.model import Incidente
from app.operaciones.talleres.model import Taller
from app.administracion.usuarios.model import Cliente, Usuario
from app.gestion_servicios.pagos.model import Pago
from app.bitacora_reportes.reportes.schemas import (
    ResumenGeneral, ReporteIncidentes, ItemIncidente,
    ReporteUsuarios, ItemUsuario,
    ReporteTalleres, ItemTaller,
    ReportePagos, ItemPago,
)
from google import genai


logger = logging.getLogger(__name__)


def _parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def _audio_intencion_local(texto: str | None) -> str:
    value = (texto or "").lower()
    if any(w in value for w in ("usuario", "usuarios", "cliente", "clientes", "admin", "administrador")):
        return "usuarios"
    if any(w in value for w in ("pago", "pagos", "cobro", "cobros", "ingreso", "ingresos", "qr")):
        return "pagos"
    if any(w in value for w in ("incidente", "incidentes", "caso", "casos", "alerta", "alertas")):
        return "incidentes"
    if any(w in value for w in ("taller", "talleres", "mecanico", "mecanicos")):
        return "talleres"
    if any(w in value for w in ("resumen", "general", "principal", "dashboard")):
        return "resumen"
    return "desconocido"


def _upload_and_wait_audio(client: genai.Client, audio_path: str):
    try:
        audio_file = client.files.upload(file=audio_path)
        deadline = time.time() + 60
        while (
            getattr(audio_file, "state", None)
            and str(audio_file.state) in ("FileState.PROCESSING", "PROCESSING")
            and time.time() < deadline
        ):
            time.sleep(2)
            audio_file = client.files.get(name=audio_file.name)

        state_str = str(getattr(audio_file, "state", "ACTIVE"))
        if "ACTIVE" in state_str:
            return audio_file
    except Exception as exc:
        logger.warning("No se pudo subir audio de reporte a Gemini: %s", exc)
    return None


async def analizar_audio_reporte(audio_path: str) -> dict[str, str | None]:
    api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {
            "intencion": "desconocido",
            "transcripcion": None,
            "respuesta_ia": "GEMINI_API_KEY no esta configurada; no se pudo interpretar el audio.",
        }

    try:
        client = genai.Client(api_key=api_key)
        audio_ref = await asyncio.to_thread(_upload_and_wait_audio, client, audio_path)
        if not audio_ref:
            return {
                "intencion": "desconocido",
                "transcripcion": None,
                "respuesta_ia": "No se pudo preparar el audio para IA.",
            }

        prompt = """Transcribe el audio del administrador y detecta que reporte quiere abrir.

Intenciones validas:
- usuarios
- pagos
- incidentes
- talleres
- resumen
- desconocido

Ejemplos:
"quiero el reporte de usuario" => usuarios
"mostrame pagos" => pagos
"reporte de casos" => incidentes
"reporte de talleres" => talleres

Responde solo en este formato, sin markdown:
INTENCION: <una intencion valida>
TRANSCRIPCION: <texto escuchado>
RESPUESTA: <mensaje breve para mostrar en la app>"""

        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-2.5-flash",
            contents=[audio_ref, prompt],
        )
        text = (response.text or "").strip()
        parsed: dict[str, str | None] = {
            "intencion": "desconocido",
            "transcripcion": None,
            "respuesta_ia": text or "Audio analizado.",
        }
        for line in text.splitlines():
            clean = line.strip().replace("*", "")
            if clean.upper().startswith("INTENCION:"):
                parsed["intencion"] = clean.split(":", 1)[1].strip().lower()
            elif clean.upper().startswith("TRANSCRIPCION:"):
                parsed["transcripcion"] = clean.split(":", 1)[1].strip()
            elif clean.upper().startswith("RESPUESTA:"):
                parsed["respuesta_ia"] = clean.split(":", 1)[1].strip()

        parsed["intencion"] = _audio_intencion_local(parsed.get("intencion")) if parsed.get("intencion") not in {
            "usuarios", "pagos", "incidentes", "talleres", "resumen", "desconocido"
        } else parsed.get("intencion")
        if parsed["intencion"] == "desconocido":
            parsed["intencion"] = _audio_intencion_local(parsed.get("transcripcion"))
        return parsed
    except Exception as exc:
        logger.warning("No se pudo interpretar audio de reporte con IA: %s", exc)
        return {
            "intencion": "desconocido",
            "transcripcion": None,
            "respuesta_ia": f"No se pudo interpretar el audio con IA: {exc}",
        }


async def resumen_general(db: AsyncSession, id_tenant: int) -> ResumenGeneral:
    estados = ["REPORTADO", "EN_PROCESO", "RESUELTO", "PAGADO", "CANCELADO"]
    conteos: dict[str, int] = {}
    for est in estados:
        r = await db.execute(
            select(func.count()).where(Incidente.estado == est, Incidente.id_tenant == id_tenant).select_from(Incidente)
        )
        conteos[est] = r.scalar_one()
    total_inc = sum(conteos.values())

    r_users   = await db.execute(select(func.count()).where(Usuario.id_tenant == id_tenant).select_from(Usuario))
    r_clients = await db.execute(select(func.count()).where(Cliente.id_tenant == id_tenant).select_from(Cliente))
    r_talleres = await db.execute(
        select(func.count()).where(Taller.estado_registro == "APROBADO", Taller.id_tenant == id_tenant).select_from(Taller)
    )

    r_pagos = await db.execute(
        select(func.count()).where(Pago.estado == "COMPLETADO", Pago.id_tenant == id_tenant).select_from(Pago)
    )
    r_ingresos = await db.execute(
        select(func.sum(Pago.monto_total)).where(Pago.estado == "COMPLETADO", Pago.id_tenant == id_tenant)
    )
    r_comision = await db.execute(
        select(func.sum(Pago.comision_plataforma)).where(Pago.estado == "COMPLETADO", Pago.id_tenant == id_tenant)
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


async def reporte_incidentes(
    db: AsyncSession,
    id_tenant: int,
    desde: str | None = None,
    hasta: str | None = None,
    estado: str | None = None,
    id_taller: int | None = None,
) -> ReporteIncidentes:
    stmt = select(Incidente, Taller.razon_social).outerjoin(Taller, Incidente.id_taller == Taller.id_taller).where(Incidente.id_tenant == id_tenant)

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


async def reporte_usuarios(
    db: AsyncSession,
    id_tenant: int,
    desde: str | None = None,
    hasta: str | None = None,
    rol: str | None = None,
) -> ReporteUsuarios:
    stmt = (
        select(Usuario)
        .where(Usuario.id_tenant == id_tenant)
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


async def reporte_talleres(db: AsyncSession, id_tenant: int) -> ReporteTalleres:
    talleres_r = await db.execute(select(Taller).where(Taller.id_tenant == id_tenant))
    talleres = talleres_r.scalars().all()

    items: list[ItemTaller] = []
    total_ingresos = Decimal("0")

    for t in talleres:
        r_total = await db.execute(
            select(func.count()).where(Incidente.id_taller == t.id_taller, Incidente.id_tenant == id_tenant).select_from(Incidente)
        )
        total_svc = r_total.scalar_one()

        r_comp = await db.execute(
            select(func.count()).where(
                Incidente.id_taller == t.id_taller,
                Incidente.id_tenant == id_tenant,
                Incidente.estado.in_(["RESUELTO", "PAGADO"])
            ).select_from(Incidente)
        )
        comp_svc = r_comp.scalar_one()

        sub_inc = select(Incidente.id_incidente).where(Incidente.id_taller == t.id_taller, Incidente.id_tenant == id_tenant)
        r_ing = await db.execute(
            select(func.sum(Pago.monto_taller)).where(
                Pago.id_incidente.in_(sub_inc),
                Pago.id_tenant == id_tenant,
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


async def reporte_pagos(
    db: AsyncSession,
    id_tenant: int,
    desde: str | None = None,
    hasta: str | None = None,
    estado: str | None = None,
    metodo: str | None = None,
) -> ReportePagos:
    stmt = select(Pago).where(Pago.id_tenant == id_tenant).order_by(Pago.created_at.desc())

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

    monto_total    = sum((it.monto_total for it in items), Decimal("0"))
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
