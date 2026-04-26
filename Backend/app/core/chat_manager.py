from fastapi import WebSocket
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class ChatManager:
    """Gestor de salas de chat basadas en id_incidente."""

    def __init__(self):
        # room_id (id_incidente) -> { id_usuario: WebSocket }
        self._rooms: Dict[int, Dict[int, WebSocket]] = {}

    async def join(self, ws: WebSocket, id_incidente: int, id_usuario: int):
        await ws.accept()
        room = self._rooms.setdefault(id_incidente, {})
        room[id_usuario] = ws
        logger.info(f"[Chat] Usuario {id_usuario} entró a sala {id_incidente} ({len(room)} participantes)")

    def leave(self, id_incidente: int, id_usuario: int):
        room = self._rooms.get(id_incidente, {})
        room.pop(id_usuario, None)
        if not room:
            self._rooms.pop(id_incidente, None)
        logger.info(f"[Chat] Usuario {id_usuario} salió de sala {id_incidente}")

    async def broadcast(self, id_incidente: int, data: dict):
        """Envía un mensaje a todos los participantes de la sala."""
        room = self._rooms.get(id_incidente, {})
        dead: List[int] = []
        for uid, ws in room.items():
            try:
                await ws.send_json(data)
            except Exception as exc:
                logger.warning(f"[Chat] Error enviando a usuario {uid} en sala {id_incidente}: {exc}")
                dead.append(uid)
        for uid in dead:
            room.pop(uid, None)

    def participantes_en_linea(self, id_incidente: int) -> int:
        return len(self._rooms.get(id_incidente, {}))


chat_manager = ChatManager()
