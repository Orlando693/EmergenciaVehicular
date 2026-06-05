from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class PlanOut(BaseModel):
    id_plan: int
    slug: str
    nombre: str
    descripcion: str | None
    precio: Decimal
    moneda: str
    max_incidentes_mes: int
    max_tecnicos: int
    max_usuarios: int
    tiene_ia: bool
    tiene_reportes_avanzados: bool
    tiene_soporte_prioritario: bool
    tiene_notificaciones_push: bool
    orden: int
    estado: str

    model_config = {"from_attributes": True}


class SuscripcionOut(BaseModel):
    id_suscripcion: int
    id_tenant: int
    id_plan: int
    estado: str
    es_trial: bool
    fecha_inicio: datetime
    fecha_fin: datetime | None
    plan: PlanOut

    model_config = {"from_attributes": True}


class SuscribirRequest(BaseModel):
    id_plan: int
