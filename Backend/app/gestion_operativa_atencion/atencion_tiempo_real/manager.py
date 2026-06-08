import logging
from datetime import datetime, timezone
from typing import Dict, List

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class AtencionRealtimeManager:
    """Salas WebSocket por incidente para seguimiento de atencion."""

    def __init__(self) -> None:
        self._rooms: Dict[int, Dict[int, WebSocket]] = {}
        self._last_locations: Dict[int, dict] = {}

    async def join(self, ws: WebSocket, id_incidente: int, id_usuario: int) -> None:
        await ws.accept()
        room = self._rooms.setdefault(id_incidente, {})
        room[id_usuario] = ws
        logger.info("[CU18] Usuario %s conectado a incidente %s", id_usuario, id_incidente)

    def leave(self, id_incidente: int, id_usuario: int) -> None:
        room = self._rooms.get(id_incidente, {})
        room.pop(id_usuario, None)
        if not room:
            self._rooms.pop(id_incidente, None)
        logger.info("[CU18] Usuario %s salio de incidente %s", id_usuario, id_incidente)

    async def broadcast(self, id_incidente: int, data: dict) -> None:
        room = self._rooms.get(id_incidente, {})
        dead: List[int] = []
        for id_usuario, ws in room.items():
            try:
                await ws.send_json(data)
            except Exception as exc:
                logger.warning("[CU18] Error WS usuario=%s incidente=%s: %s", id_usuario, id_incidente, exc)
                dead.append(id_usuario)
        for id_usuario in dead:
            room.pop(id_usuario, None)

    def participantes_en_linea(self, id_incidente: int) -> int:
        return len(self._rooms.get(id_incidente, {}))

    def set_location(self, id_incidente: int, data: dict) -> dict:
        data = {**data, "updated_at": datetime.now(timezone.utc).isoformat()}
        self._last_locations[id_incidente] = data
        return data

    def get_location(self, id_incidente: int) -> dict | None:
        return self._last_locations.get(id_incidente)


atencion_realtime_manager = AtencionRealtimeManager()
