from datetime import datetime
from pydantic import BaseModel, Field


class BackupRegistroOut(BaseModel):
    id_backup:      int
    id_tenant:      int
    id_usuario:     int | None
    tipo:           str
    estado:         str
    nombre_archivo: str | None
    tamano_bytes:   int
    created_at:     datetime

    model_config = {"from_attributes": True}


class BackupConfigOut(BaseModel):
    id_config:       int
    id_tenant:       int
    activo:          bool
    frecuencia:      str
    hora:            str
    proximo_backup:  datetime | None
    ultimo_backup:   datetime | None
    updated_at:      datetime

    model_config = {"from_attributes": True}


class BackupConfigUpdate(BaseModel):
    activo:    bool
    frecuencia: str = Field(default="DIARIO", pattern="^(DIARIO|SEMANAL|MENSUAL)$")
    hora:      str  = Field(default="02:00", pattern=r"^\d{2}:\d{2}$")
