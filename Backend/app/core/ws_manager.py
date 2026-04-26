from fastapi import WebSocket
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Gestor de conexiones WebSocket por usuario."""

    def __init__(self):
        self._connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, ws: WebSocket, id_usuario: int):
        await ws.accept()
        self._connections.setdefault(id_usuario, []).append(ws)
        logger.info(f"[WS] Usuario {id_usuario} conectado ({self._total()} conexiones activas)")

    def disconnect(self, ws: WebSocket, id_usuario: int):
        conns = self._connections.get(id_usuario, [])
        if ws in conns:
            conns.remove(ws)
        if not conns:
            self._connections.pop(id_usuario, None)
        logger.info(f"[WS] Usuario {id_usuario} desconectado ({self._total()} conexiones activas)")

    async def push(self, id_usuario: int, data: dict):
        """Envía un mensaje JSON a todas las conexiones del usuario."""
        conns = self._connections.get(id_usuario, [])
        if not conns:
            return
        dead: List[WebSocket] = []
        for ws in conns:
            try:
                await ws.send_json(data)
            except Exception as exc:
                logger.warning(f"[WS] Error enviando a usuario {id_usuario}: {exc}")
                dead.append(ws)
        for ws in dead:
            conns.remove(ws)

    def _total(self) -> int:
        return sum(len(v) for v in self._connections.values())


ws_manager = WebSocketManager()
