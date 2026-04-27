from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional


class NotificacionOut(BaseModel):
    id_notificacion: int
    id_usuario: int
    id_incidente: Optional[int] = None
    titulo: str
    mensaje: str
    tipo: str
    leida: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificacionPage(BaseModel):
    items: List[NotificacionOut]
    total: int
    no_leidas: int


class FCMTokenIn(BaseModel):
    token: str
    platform: Optional[str] = None


class FCMTokenOut(BaseModel):
    id_dispositivo: int
    id_usuario: int
    fcm_token: str
    platform: Optional[str] = None
    activo: bool

    model_config = {"from_attributes": True}
