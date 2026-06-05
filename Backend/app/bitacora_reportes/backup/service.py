import json
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.bitacora_reportes.backup.model import BackupConfig, BackupRegistro
from app.bitacora_reportes.backup.schemas import BackupConfigUpdate


# ── helpers ────────────────────────────────────────────────────────────────────

def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _calcular_proximo(config: BackupConfig) -> datetime:
    hora_h, hora_m = map(int, config.hora.split(":"))
    base = _utc_now().replace(hour=hora_h, minute=hora_m, second=0, microsecond=0)
    if config.frecuencia == "DIARIO":
        delta = timedelta(days=1)
    elif config.frecuencia == "SEMANAL":
        delta = timedelta(weeks=1)
    else:  # MENSUAL
        delta = timedelta(days=30)
    return base + delta


def _serialize(obj: any) -> any:
    """Convierte objetos SQLAlchemy a dicts serializables."""
    if obj is None:
        return None
    if hasattr(obj, "__table__"):
        return {c.key: _serialize(getattr(obj, c.key)) for c in obj.__table__.columns}
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj


# ── recolectar datos del tenant ────────────────────────────────────────────────

async def _recolectar_datos(id_tenant: int, db: AsyncSession) -> dict:
    """Extrae todos los datos relevantes del tenant en un dict serializable."""
    from app.administracion.usuarios.model import Usuario, Cliente
    from app.operaciones.talleres.model import Taller
    from app.operaciones.tecnicos.model import Tecnico
    from app.gestion_vehiculos.vehiculos.model import Vehiculo
    from app.gestion_incidentes.incidentes.model import Incidente
    from app.gestion_servicios.pagos.model import Pago
    from app.bitacora_reportes.bitacora.model import Bitacora

    async def fetch(model, extra_filters=None):
        q = select(model).where(model.id_tenant == id_tenant)
        if extra_filters:
            for f in extra_filters:
                q = q.where(f)
        res = await db.execute(q)
        return [_serialize(r) for r in res.scalars().all()]

    return {
        "tenant_id":    id_tenant,
        "generado_en":  _utc_now().isoformat(),
        "version":      "1.0",
        "usuarios":     await fetch(Usuario),
        "clientes":     await fetch(Cliente),
        "talleres":     await fetch(Taller),
        "tecnicos":     await fetch(Tecnico),
        "vehiculos":    await fetch(Vehiculo),
        "incidentes":   await fetch(Incidente),
        "pagos":        await fetch(Pago),
        "bitacora":     await fetch(Bitacora),
    }


# ── operaciones ────────────────────────────────────────────────────────────────

async def generar_backup(
    id_tenant:  int,
    id_usuario: int,
    tipo:       str,
    db:         AsyncSession,
) -> BackupRegistro:
    datos = await _recolectar_datos(id_tenant, db)
    datos_json = json.dumps(datos, ensure_ascii=False, default=str)
    tamano = len(datos_json.encode("utf-8"))

    nombre = f"backup_{id_tenant}_{_utc_now().strftime('%Y%m%d_%H%M%S')}.json"
    registro = BackupRegistro(
        id_tenant=id_tenant,
        id_usuario=id_usuario,
        tipo=tipo,
        estado="COMPLETADO",
        nombre_archivo=nombre,
        tamano_bytes=tamano,
        datos_json=datos_json,
    )
    db.add(registro)
    await db.commit()
    await db.refresh(registro)
    return registro


async def listar_backups(id_tenant: int, db: AsyncSession) -> list:
    q = (
        select(BackupRegistro)
        .where(BackupRegistro.id_tenant == id_tenant)
        .order_by(BackupRegistro.created_at.desc())
        .limit(50)
    )
    res = await db.execute(q)
    return res.scalars().all()


async def descargar_backup(id_backup: int, id_tenant: int, db: AsyncSession) -> str:
    res = await db.execute(
        select(BackupRegistro).where(
            BackupRegistro.id_backup == id_backup,
            BackupRegistro.id_tenant == id_tenant,
        )
    )
    reg = res.scalar_one_or_none()
    if not reg:
        raise HTTPException(status_code=404, detail="Backup no encontrado")
    if not reg.datos_json:
        raise HTTPException(status_code=404, detail="Datos del backup no disponibles")
    return reg.datos_json


async def eliminar_backup(id_backup: int, id_tenant: int, db: AsyncSession) -> None:
    res = await db.execute(
        select(BackupRegistro).where(
            BackupRegistro.id_backup == id_backup,
            BackupRegistro.id_tenant == id_tenant,
        )
    )
    reg = res.scalar_one_or_none()
    if not reg:
        raise HTTPException(status_code=404, detail="Backup no encontrado")
    await db.delete(reg)
    await db.commit()


# ── configuración automática ───────────────────────────────────────────────────

async def obtener_config(id_tenant: int, db: AsyncSession) -> BackupConfig:
    res = await db.execute(
        select(BackupConfig).where(BackupConfig.id_tenant == id_tenant)
    )
    cfg = res.scalar_one_or_none()
    if cfg:
        return cfg

    try:
        cfg = BackupConfig(id_tenant=id_tenant)
        db.add(cfg)
        await db.commit()
        await db.refresh(cfg)
        return cfg
    except IntegrityError:
        # Race condition: otro request creó el registro justo antes
        await db.rollback()
        res = await db.execute(
            select(BackupConfig).where(BackupConfig.id_tenant == id_tenant)
        )
        return res.scalar_one()


async def actualizar_config(
    id_tenant: int,
    data: BackupConfigUpdate,
    db: AsyncSession,
) -> BackupConfig:
    cfg = await obtener_config(id_tenant, db)
    cfg.activo    = data.activo
    cfg.frecuencia = data.frecuencia
    cfg.hora      = data.hora
    if data.activo:
        cfg.proximo_backup = _calcular_proximo(cfg)
    await db.commit()
    await db.refresh(cfg)
    return cfg


async def verificar_y_ejecutar_auto(id_tenant: int, id_usuario: int, db: AsyncSession) -> BackupRegistro | None:
    """Comprueba si hay un backup automático pendiente y lo ejecuta si es necesario."""
    cfg = await obtener_config(id_tenant, db)
    if not cfg.activo or not cfg.proximo_backup:
        return None
    if _utc_now() < cfg.proximo_backup:
        return None

    reg = await generar_backup(id_tenant, id_usuario, "AUTOMATICO", db)
    cfg.ultimo_backup  = _utc_now()
    cfg.proximo_backup = _calcular_proximo(cfg)
    await db.commit()
    return reg
