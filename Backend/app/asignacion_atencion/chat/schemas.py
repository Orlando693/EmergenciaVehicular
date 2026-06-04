from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, field_validator


class MensajeOut(BaseModel):
    id_mensaje:    int
    id_incidente:  int
    id_usuario:    Optional[int] = None
    contenido:     str
    nombre_emisor: str
    rol_emisor:    str
    created_at:    datetime

    model_config = {"from_attributes": True}


class ChatHistorial(BaseModel):
    mensajes: List[MensajeOut]
    total:    int
    en_linea: int = 0
