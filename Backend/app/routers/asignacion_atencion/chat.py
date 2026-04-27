from datetime import datetime, timezone

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.chat_manager import chat_manager
from app.core.dependencies import DBDep, CurrentUser
from app.core.security import decode_token
from app.database import AsyncSessionLocal
from app.models.usuario import Usuario
from app.schemas.mensaje_chat import ChatHistorial, MensajeOut
from app.services import chat_service

router = APIRouter(prefix="/chat", tags=["Chat", "CU15"])


# ── REST ──────────────────────────────────────────────────────────────────────

@router.get("/{id_incidente}", response_model=ChatHistorial)
async def obtener_historial(
    id_incidente: int,
    db: DBDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
):
    """Obtiene el historial de mensajes de un incidente."""
    rol = current_user.roles[0].nombre if current_user.roles else "DESCONOCIDO"
    await chat_service.verificar_acceso_chat(id_incidente, current_user.id_usuario, rol, db)
    data = await chat_service.obtener_mensajes(id_incidente, db, skip=skip, limit=limit)
    data["en_linea"] = chat_manager.participantes_en_linea(id_incidente)
    return data


# ── WebSocket ─────────────────────────────────────────────────────────────────

@router.websocket("/{id_incidente}/ws")
async def ws_chat(id_incidente: int, ws: WebSocket, token: str = Query(...)):
    """
    Conexión WebSocket de chat en tiempo real para un incidente.
    El cliente envía el JWT como query param: ?token=<access_token>
    Mensajes entrantes (JSON): { "contenido": "texto" }
    Mensajes salientes (JSON):
      - tipo "mensaje": { tipo, id_mensaje, id_usuario, nombre_emisor, rol_emisor, contenido, created_at }
      - tipo "sistema": { tipo, contenido, created_at }
    """
    # 1. Autenticar
    try:
        token_data = decode_token(token)
    except Exception:
        await ws.close(code=1008)
        return

    id_usuario = token_data.id_usuario

    # 2. Cargar usuario y verificar acceso
    async with AsyncSessionLocal() as db:
        r = await db.execute(
            select(Usuario)
            .where(Usuario.id_usuario == id_usuario)
            .options(selectinload(Usuario.roles))
        )
        usuario = r.scalar_one_or_none()
        if not usuario:
            await ws.close(code=1008)
            return

        rol = usuario.roles[0].nombre if usuario.roles else "DESCONOCIDO"
        nombre = f"{usuario.nombres} {usuario.apellidos}".strip()

        try:
            await chat_service.verificar_acceso_chat(id_incidente, id_usuario, rol, db)
        except HTTPException:
            await ws.close(code=1008)
            return

    # 3. Unirse a la sala
    await chat_manager.join(ws, id_incidente, id_usuario)

    await chat_manager.broadcast(id_incidente, {
        "tipo": "sistema",
        "contenido": f"{nombre} se unió al chat",
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    # 4. Bucle de mensajes
    try:
        while True:
            data = await ws.receive_json()
            contenido = str(data.get("contenido", "")).strip()
            if not contenido or len(contenido) > 2000:
                continue

            async with AsyncSessionLocal() as db:
                msg = await chat_service.crear_mensaje(
                    id_incidente=id_incidente,
                    id_usuario=id_usuario,
                    contenido=contenido,
                    nombre_emisor=nombre,
                    rol_emisor=rol,
                    db=db,
                )

            await chat_manager.broadcast(id_incidente, {
                "tipo":          "mensaje",
                "id_mensaje":    msg.id_mensaje,
                "id_usuario":    msg.id_usuario,
                "nombre_emisor": msg.nombre_emisor,
                "rol_emisor":    msg.rol_emisor,
                "contenido":     msg.contenido,
                "created_at":    msg.created_at.isoformat(),
            })

    except WebSocketDisconnect:
        chat_manager.leave(id_incidente, id_usuario)
        await chat_manager.broadcast(id_incidente, {
            "tipo":      "sistema",
            "contenido": f"{nombre} salió del chat",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
