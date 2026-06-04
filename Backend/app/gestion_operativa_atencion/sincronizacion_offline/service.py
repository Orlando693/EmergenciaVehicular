import logging

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.bitacora_reportes.bitacora.model import Bitacora
from app.gestion_operativa_atencion.sincronizacion_offline.model import EmergenciaOfflineSync
from app.administracion.usuarios.model import Usuario
from app.gestion_operativa_atencion.sincronizacion_offline.schemas import EmergenciaOfflineSyncOut, EmergenciaOfflineSyncRequest
from app.asignacion_atencion.notificaciones import service as notificacion_service
from app.gestion_incidentes.incidentes import service as incidente_service

logger = logging.getLogger(__name__)


async def sincronizar_emergencia_offline(
    db: AsyncSession,
    usuario: Usuario,
    payload: EmergenciaOfflineSyncRequest,
) -> EmergenciaOfflineSyncOut:
    cliente = await incidente_service.get_cliente_by_usuario_id(usuario.id_usuario, usuario.id_tenant, db)
    registro = await _buscar_sync(db, usuario.id_tenant, cliente.id_cliente, payload.client_sync_id)

    if registro and registro.id_incidente:
        incidente = await incidente_service.obtener_detalle_incidente(
            registro.id_incidente,
            usuario.id_usuario,
            es_admin=False,
            es_taller=False,
            db=db,
            id_tenant=usuario.id_tenant,
        )
        return _sync_out(registro, incidente, "La emergencia ya fue sincronizada previamente")

    if registro is None:
        registro = EmergenciaOfflineSync(
            id_tenant=usuario.id_tenant,
            id_cliente=cliente.id_cliente,
            client_sync_id=payload.client_sync_id,
            estado_sync="PENDIENTE",
            intentos=0,
        )
        db.add(registro)
        try:
            await db.commit()
            await db.refresh(registro)
        except IntegrityError:
            await db.rollback()
            registro = await _buscar_sync(db, usuario.id_tenant, cliente.id_cliente, payload.client_sync_id)
            if registro and registro.id_incidente:
                incidente = await incidente_service.obtener_detalle_incidente(
                    registro.id_incidente,
                    usuario.id_usuario,
                    es_admin=False,
                    es_taller=False,
                    db=db,
                    id_tenant=usuario.id_tenant,
                )
                return _sync_out(registro, incidente, "La emergencia ya fue sincronizada previamente")
            if registro is None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="No se pudo reservar la sincronizacion offline",
                )

    registro.intentos = int(registro.intentos or 0) + 1
    registro.estado_sync = "PENDIENTE"
    registro.error_mensaje = None
    await db.commit()

    try:
        incidente = await incidente_service.registrar_incidente_inteligente(
            payload.emergencia,
            usuario.id_usuario,
            usuario.id_tenant,
            db,
        )
    except HTTPException as exc:
        await _marcar_error(db, registro, usuario, str(exc.detail)[:500])
        raise
    except Exception as exc:
        logger.exception("CU19 fallo al sincronizar emergencia offline: %s", exc)
        await _marcar_error(db, registro, usuario, "Error interno al sincronizar emergencia")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo sincronizar la emergencia. Permanece pendiente para reintento.",
        )

    registro.id_incidente = incidente.id_incidente
    registro.estado_sync = "SINCRONIZADA"
    registro.error_mensaje = None
    db.add(
        Bitacora(
            id_tenant=usuario.id_tenant,
            modulo="CU19 Sincronizacion offline",
            accion=f"Emergencia offline sincronizada como incidente #{incidente.id_incidente}",
            rol="CLIENTE",
            usuario_email=usuario.email,
            id_usuario=usuario.id_usuario,
        )
    )
    await db.commit()
    await db.refresh(registro)

    await _notificar_resultado(db, usuario, registro, incidente.id_incidente)
    return _sync_out(registro, incidente, "Emergencia sincronizada correctamente")


async def obtener_estado_sincronizacion(
    db: AsyncSession,
    usuario: Usuario,
    client_sync_id: str,
) -> EmergenciaOfflineSyncOut:
    cliente = await incidente_service.get_cliente_by_usuario_id(usuario.id_usuario, usuario.id_tenant, db)
    registro = await _buscar_sync(db, usuario.id_tenant, cliente.id_cliente, client_sync_id)
    if not registro:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sincronizacion no encontrada")

    incidente = None
    if registro.id_incidente:
        incidente = await incidente_service.obtener_detalle_incidente(
            registro.id_incidente,
            usuario.id_usuario,
            es_admin=False,
            es_taller=False,
            db=db,
            id_tenant=usuario.id_tenant,
        )
    return _sync_out(registro, incidente, "Estado de sincronizacion obtenido")


async def _buscar_sync(
    db: AsyncSession,
    id_tenant: int,
    id_cliente: int,
    client_sync_id: str,
) -> EmergenciaOfflineSync | None:
    result = await db.execute(
        select(EmergenciaOfflineSync).where(
            EmergenciaOfflineSync.id_tenant == id_tenant,
            EmergenciaOfflineSync.id_cliente == id_cliente,
            EmergenciaOfflineSync.client_sync_id == client_sync_id,
        )
    )
    return result.scalar_one_or_none()


async def _marcar_error(db: AsyncSession, registro: EmergenciaOfflineSync, usuario: Usuario, mensaje: str) -> None:
    registro.estado_sync = "ERROR"
    registro.error_mensaje = mensaje
    db.add(
        Bitacora(
            id_tenant=usuario.id_tenant,
            modulo="CU19 Sincronizacion offline",
            accion=f"Fallo sincronizacion offline client_sync_id={registro.client_sync_id}",
            rol="CLIENTE",
            usuario_email=usuario.email,
            id_usuario=usuario.id_usuario,
        )
    )
    await db.commit()


async def _notificar_resultado(
    db: AsyncSession,
    usuario: Usuario,
    registro: EmergenciaOfflineSync,
    id_incidente: int,
) -> None:
    try:
        await notificacion_service.crear_notificacion(
            db=db,
            id_usuario=usuario.id_usuario,
            titulo="Emergencia sincronizada",
            mensaje=f"Tu emergencia pendiente fue registrada como incidente #{id_incidente}.",
            tipo="SINCRONIZACION_OFFLINE",
            id_incidente=id_incidente,
            id_tenant=registro.id_tenant,
        )
    except Exception as exc:
        logger.warning("No se pudo notificar resultado CU19: %s", exc)


def _sync_out(
    registro: EmergenciaOfflineSync,
    incidente,
    mensaje: str,
) -> EmergenciaOfflineSyncOut:
    return EmergenciaOfflineSyncOut(
        client_sync_id=registro.client_sync_id,
        estado_sync=registro.estado_sync,
        id_incidente=registro.id_incidente,
        incidente=incidente,
        mensaje=mensaje,
        error_mensaje=registro.error_mensaje,
        intentos=int(registro.intentos or 0),
        created_at=registro.created_at,
        updated_at=registro.updated_at,
    )
