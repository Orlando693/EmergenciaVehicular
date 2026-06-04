from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Annotated

from app.core.dependencies import DBDep, CurrentUser, require_roles
from app.core.ws_manager import ws_manager
from app.core.security import decode_token
from app.database import AsyncSessionLocal
from app.administracion.usuarios.model import Usuario
from app.asignacion_atencion.notificaciones.schemas import FCMTokenIn, FCMTokenOut, NotificacionOut, NotificacionPage
from app.asignacion_atencion.notificaciones import service as notificacion_service

router = APIRouter(prefix="/notificaciones", tags=["Notificaciones", "CU14"])


@router.post("/fcm-token", response_model=FCMTokenOut, status_code=status.HTTP_201_CREATED)
async def registrar_fcm_token(
    payload: FCMTokenIn,
    db: DBDep,
    current_user: CurrentUser,
):
    return await notificacion_service.registrar_fcm_token(
        db,
        current_user.id_usuario,
        current_user.id_tenant,
        payload.token,
        payload.platform,
    )


@router.get("", response_model=NotificacionPage)
async def listar_notificaciones(
    db: DBDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 20,
):
    return await notificacion_service.listar_notificaciones(
        db, current_user.id_usuario, current_user.id_tenant, skip=skip, limit=limit
    )


@router.get("/no-leidas")
async def contar_no_leidas(db: DBDep, current_user: CurrentUser):
    count = await notificacion_service.contar_no_leidas(db, current_user.id_usuario, current_user.id_tenant)
    return {"count": count}


@router.patch("/{id_notificacion}/leer", response_model=NotificacionOut)
async def marcar_leida(id_notificacion: int, db: DBDep, current_user: CurrentUser):
    ok = await notificacion_service.marcar_leida(db, id_notificacion, current_user.id_usuario, current_user.id_tenant)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notificacion no encontrada")
    from sqlalchemy import select
    from app.asignacion_atencion.notificaciones.model import Notificacion
    r = await db.execute(
        select(Notificacion).where(Notificacion.id_notificacion == id_notificacion, Notificacion.id_tenant == current_user.id_tenant)
    )
    return r.scalar_one()


@router.patch("/leer-todas")
async def marcar_todas_leidas(db: DBDep, current_user: CurrentUser):
    await notificacion_service.marcar_todas_leidas(db, current_user.id_usuario, current_user.id_tenant)
    return {"message": "Todas las notificaciones marcadas como leidas"}


@router.websocket("/ws")
async def ws_notificaciones(ws: WebSocket, token: str = Query(...)):
    """
    WebSocket autenticado para recibir notificaciones en tiempo real.
    Valida JWT y tenant antes de aceptar la conexión.
    """
    try:
        token_data = decode_token(token)
    except Exception:
        await ws.close(code=1008)
        return

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Usuario)
            .where(Usuario.id_usuario == token_data.id_usuario)
            .options(selectinload(Usuario.roles))
        )
        usuario = result.scalar_one_or_none()
        if (
            not usuario
            or usuario.id_tenant is None
            or token_data.id_tenant is None
            or int(usuario.id_tenant) != int(token_data.id_tenant)
        ):
            await ws.close(code=1008)
            return

    await ws_manager.connect(ws, token_data.id_usuario)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(ws, token_data.id_usuario)
