from fastapi import APIRouter, Depends, Response

from app.core.dependencies import CurrentUser, DBDep, require_roles
from app.bitacora_reportes.backup import service as backup_service
from app.bitacora_reportes.backup.schemas import BackupConfigOut, BackupConfigUpdate, BackupRegistroOut

router = APIRouter(prefix="/backup", tags=["Backup (CU)"])

_ROLES = Depends(require_roles("ADMINISTRADOR", "TALLER"))


@router.post(
    "",
    response_model=BackupRegistroOut,
    status_code=201,
    summary="Generar backup manual del tenant",
    dependencies=[_ROLES],
)
async def generar_backup_manual(current_user: CurrentUser, db: DBDep):
    """Genera y almacena un backup JSON con todos los datos del tenant."""
    return await backup_service.generar_backup(
        current_user.id_tenant, current_user.id_usuario, "MANUAL", db
    )


@router.get(
    "",
    response_model=list[BackupRegistroOut],
    summary="Listar historial de backups",
    dependencies=[_ROLES],
)
async def listar_backups(current_user: CurrentUser, db: DBDep):
    return await backup_service.listar_backups(current_user.id_tenant, db)


@router.get(
    "/{id_backup}/descargar",
    summary="Descargar archivo JSON de un backup",
    dependencies=[_ROLES],
)
async def descargar_backup(id_backup: int, current_user: CurrentUser, db: DBDep):
    datos = await backup_service.descargar_backup(id_backup, current_user.id_tenant, db)
    return Response(
        content=datos,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="backup_{id_backup}.json"'},
    )


@router.delete(
    "/{id_backup}",
    status_code=204,
    summary="Eliminar backup del historial",
    dependencies=[_ROLES],
)
async def eliminar_backup(id_backup: int, current_user: CurrentUser, db: DBDep):
    await backup_service.eliminar_backup(id_backup, current_user.id_tenant, db)


@router.get(
    "/config",
    response_model=BackupConfigOut,
    summary="Obtener configuración de backup automático",
    dependencies=[_ROLES],
)
async def obtener_config(current_user: CurrentUser, db: DBDep):
    return await backup_service.obtener_config(current_user.id_tenant, db)


@router.put(
    "/config",
    response_model=BackupConfigOut,
    summary="Actualizar configuración de backup automático",
    dependencies=[_ROLES],
)
async def actualizar_config(data: BackupConfigUpdate, current_user: CurrentUser, db: DBDep):
    return await backup_service.actualizar_config(current_user.id_tenant, data, db)


@router.post(
    "/check-auto",
    summary="Verificar y ejecutar backup automático si está pendiente",
    dependencies=[_ROLES],
)
async def check_auto_backup(current_user: CurrentUser, db: DBDep):
    """Llamado por el frontend al cargar la página para ejecutar backups pendientes."""
    reg = await backup_service.verificar_y_ejecutar_auto(
        current_user.id_tenant, current_user.id_usuario, db
    )
    if reg:
        return {"ejecutado": True, "id_backup": reg.id_backup, "nombre": reg.nombre_archivo}
    return {"ejecutado": False}
