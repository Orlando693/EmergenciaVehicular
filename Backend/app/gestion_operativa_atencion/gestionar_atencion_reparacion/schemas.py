from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class EstimacionAtencionCreate(BaseModel):
    """Paso 4-5 del flujo: el taller registra las estimaciones iniciales."""

    tiempo_llegada: str | None = Field(
        None,
        max_length=150,
        examples=["15 minutos", "~30 min"],
        description="Tiempo estimado de llegada al lugar de la emergencia",
    )
    tiempo_reparacion: str | None = Field(
        None,
        max_length=150,
        examples=["2 horas", "aproximadamente 3 h"],
        description="Tiempo estimado de reparación del vehículo",
    )
    observacion: str | None = Field(
        None,
        max_length=1000,
        description="Observaciones adicionales para el cliente",
    )

    @model_validator(mode="after")
    def al_menos_un_campo(self) -> "EstimacionAtencionCreate":
        if not self.tiempo_llegada and not self.tiempo_reparacion:
            raise ValueError(
                "Debe indicar al menos el tiempo de llegada o el tiempo de reparación"
            )
        return self


class EstimacionAtencionUpdate(BaseModel):
    """Paso 9 del flujo: el taller actualiza una o más estimaciones."""

    tiempo_llegada: str | None = Field(None, max_length=150)
    tiempo_reparacion: str | None = Field(None, max_length=150)
    observacion: str | None = Field(None, max_length=1000)

    @model_validator(mode="after")
    def al_menos_un_campo(self) -> "EstimacionAtencionUpdate":
        if (
            self.tiempo_llegada is None
            and self.tiempo_reparacion is None
            and self.observacion is None
        ):
            raise ValueError("Debe modificar al menos un campo")
        return self


class EstimacionAtencionOut(BaseModel):
    """Respuesta con la estimación vigente del incidente."""

    id_estimacion: int
    id_incidente: int
    id_taller: int

    tiempo_llegada: str | None = None
    tiempo_reparacion: str | None = None
    observacion: str | None = None

    taller_nombre: str | None = None

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
