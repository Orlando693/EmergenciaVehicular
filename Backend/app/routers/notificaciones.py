from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query, HTTPException, status
from typing import Annotated

from app.core.dependencies import DBDep, CurrentUser, require_roles
from app.core.ws_manager import ws_manager
from app.core.security import decode_token
from app.schemas.notificacion import NotificacionOut, NotificacionPage
from app.services import notificacion_service

router = APIRouter(prefix="/notificaciones", tags=["Notificaciones", "CU14"])


@router.get("", response_model=NotificacionPage)
async def listar_notificaciones(
    db: DBDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 20,
):
    return await notificacion_service.listar_notificaciones(
        db, current_user.id_usuario, skip=skip, limit=limit
    )


@router.get("/no-leidas")
async def contar_no_leidas(db: DBDep, current_user: CurrentUser):
    count = await notificacion_service.contar_no_leidas(db, current_user.id_usuario)
    return {"count": count}


@router.patch("/{id_notificacion}/leer", response_model=NotificacionOut)
async def marcar_leida(id_notificacion: int, db: DBDep, current_user: CurrentUser):
    ok = await notificacion_service.marcar_leida(db, id_notificacion, current_user.id_usuario)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notificacion no encontrada")
    from sqlalchemy import select
    from app.models.notificacion import Notificacion
    r = await db.execute(
        select(Notificacion).where(Notificacion.id_notificacion == id_notificacion)
    )
    return r.scalar_one()


@router.patch("/leer-todas")
async def marcar_todas_leidas(db: DBDep, current_user: CurrentUser):
    await notificacion_service.marcar_todas_leidas(db, current_user.id_usuario)
    return {"message": "Todas las notificaciones marcadas como leidas"}


# ─── WebSocket ────────────────────────────────────────────────────────────────

@router.websocket("/ws")
async def ws_notificaciones(ws: WebSocket, token: str = Query(...)):
    """
    WebSocket autenticado para recibir notificaciones en tiempo real.
    El cliente envía el JWT como query param ?token=<access_token>
    """
    try:
        token_data = decode_token(token)
        id_usuario = token_data.id_usuario
    except Exception:
        await ws.close(code=1008)  # Policy violation
        return

    await ws_manager.connect(ws, id_usuario)
    try:
        while True:
            # Mantener viva la conexión; el cliente puede enviar pings
            await ws.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(ws, id_usuario)
