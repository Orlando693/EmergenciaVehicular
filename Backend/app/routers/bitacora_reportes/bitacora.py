from fastapi import APIRouter, Depends, Request
from typing import List

from app.core.dependencies import DBDep, CurrentUser, require_roles
from app.schemas.bitacora import BitacoraCreate, BitacoraResponse, BitacoraPageResponse
from app.services import bitacora_service

router = APIRouter(prefix="/bitacora", tags=["Bitácora"])


@router.get("", response_model=BitacoraPageResponse,
            dependencies=[Depends(require_roles("ADMINISTRADOR"))])
async def get_logs(db: DBDep, skip: int = 0, limit: int = 20):
    return await bitacora_service.get_logs(db, skip=skip, limit=limit)


@router.post("", response_model=BitacoraResponse)
async def create_log(
    log_data: BitacoraCreate,
    request: Request,
    db: DBDep,
    current_user: CurrentUser,
):
    client_ip = request.client.host if request.client else None
    user_rol = (
        current_user.roles[0].nombre
        if getattr(current_user, "roles", None) and len(current_user.roles) > 0
        else "DESCONOCIDO"
    )
    log_data.ip = client_ip
    log_data.rol = user_rol
    log_data.usuario_email = current_user.email
    log_data.id_usuario = current_user.id_usuario

    return await bitacora_service.create_log(db, log_data)


@router.delete("", dependencies=[Depends(require_roles("ADMINISTRADOR"))])
async def delete_all_logs(db: DBDep):
    eliminated = await bitacora_service.delete_all_logs(db)
    return {"message": f"Se eliminaron {eliminated} registros de la bitácora.", "deleted": eliminated}
