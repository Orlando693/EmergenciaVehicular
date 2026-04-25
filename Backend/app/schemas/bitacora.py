from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class BitacoraCreate(BaseModel):
    modulo: str
    accion: str
    ip: Optional[str] = None
    rol: Optional[str] = None
    usuario_email: Optional[str] = None
    id_usuario: Optional[int] = None

class BitacoraResponse(BaseModel):
    id_bitacora: int
    modulo: str
    accion: str
    ip: Optional[str] = None
    rol: Optional[str] = None
    usuario_email: Optional[str] = None
    created_at: datetime
    id_usuario: Optional[int] = None

    class Config:
        from_attributes = True

class BitacoraPageResponse(BaseModel):
    items: List[BitacoraResponse]
    total: int
