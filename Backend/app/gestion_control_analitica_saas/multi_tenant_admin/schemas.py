from datetime import datetime
from pydantic import BaseModel


class TenantInfo(BaseModel):
    id_tenant:  int
    nombre:     str
    slug:       str
    estado:     str
    created_at: datetime


class TenantUpdate(BaseModel):
    nombre: str


class UsuarioResumen(BaseModel):
    id_usuario: int
    nombres:    str
    apellidos:  str
    email:      str
    telefono:   str | None
    estado:     str
    roles:      list[str]
    created_at: datetime


class TallerResumen(BaseModel):
    id_taller:        int
    nombre_comercial: str
    estado:           str
    telefono:         str | None
    email:            str | None
    direccion:        str | None
    created_at:       datetime


class MetricasTenant(BaseModel):
    total_usuarios:     int
    total_talleres:     int
    total_clientes:     int
    total_incidentes:   int
    total_pagos:        int
    ingresos_total:     float
    incidentes_activos: int


class Aislamiento(BaseModel):
    tenants_detectados: int
    aislado:            bool
    mensaje:            str


class MultiTenantAdminOut(BaseModel):
    tenant:      TenantInfo
    metricas:    MetricasTenant
    usuarios:    list[UsuarioResumen]
    talleres:    list[TallerResumen]
    aislamiento: Aislamiento
