from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class PlatformLoginRequest(BaseModel):
    email:    str
    password: str


class PlatformTokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    nombre:       str
    email:        str
    rol:          str = "SUPERADMIN"


# ── Tenants / Organizaciones ───────────────────────────────────────────────────

class TenantPlatformOut(BaseModel):
    id_tenant:  int
    nombre:     str
    slug:       str
    estado:     str
    plan_nombre: str | None = None
    plan_slug:   str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TenantCreate(BaseModel):
    nombre: str
    slug:   str
    id_plan: int | None = None


class TenantEstadoUpdate(BaseModel):
    estado: str   # ACTIVO | SUSPENDIDO


class TenantPlanUpdate(BaseModel):
    id_plan: int


# ── Planes ────────────────────────────────────────────────────────────────────

class PlanPlatformOut(BaseModel):
    id_plan:                    int
    slug:                       str
    nombre:                     str
    descripcion:                str | None
    precio:                     Decimal
    max_incidentes_mes:         int
    max_tecnicos:               int
    max_usuarios:               int
    tiene_ia:                   bool
    tiene_reportes_avanzados:   bool
    tiene_soporte_prioritario:  bool
    tiene_notificaciones_push:  bool
    estado:                     str
    orden:                      int

    model_config = {"from_attributes": True}


class PlanCreate(BaseModel):
    slug:                       str
    nombre:                     str
    descripcion:                str = ""
    precio:                     Decimal
    max_incidentes_mes:         int = 0
    max_tecnicos:               int = 0
    max_usuarios:               int = 0
    tiene_ia:                   bool = False
    tiene_reportes_avanzados:   bool = False
    tiene_soporte_prioritario:  bool = False
    tiene_notificaciones_push:  bool = True
    orden:                      int = 99


class PlanUpdate(PlanCreate):
    pass
