from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


# ── Resumen general ───────────────────────────────────────────────────────────

class ResumenGeneral(BaseModel):
    total_incidentes:          int
    incidentes_reportados:     int
    incidentes_en_proceso:     int
    incidentes_resueltos:      int
    incidentes_pagados:        int
    incidentes_cancelados:     int
    total_usuarios:            int
    total_clientes:            int
    total_talleres:            int
    total_pagos_completados:   int
    ingresos_totales:          Decimal
    comision_plataforma_total: Decimal


# ── Incidentes ────────────────────────────────────────────────────────────────

class ItemIncidente(BaseModel):
    id_incidente:     int
    clasificacion_ia: Optional[str]
    estado:           str
    taller_nombre:    Optional[str]
    direccion:        Optional[str]
    created_at:       datetime

    model_config = {"from_attributes": True}


class ReporteIncidentes(BaseModel):
    items:     List[ItemIncidente]
    total:     int
    por_estado: Dict[str, int]


# ── Usuarios ──────────────────────────────────────────────────────────────────

class ItemUsuario(BaseModel):
    id_usuario: int
    nombres:    str
    apellidos:  str
    email:      str
    rol:        str
    estado:     str
    created_at: datetime

    model_config = {"from_attributes": True}


class ReporteUsuarios(BaseModel):
    items:   List[ItemUsuario]
    total:   int
    por_rol: Dict[str, int]


# ── Talleres ──────────────────────────────────────────────────────────────────

class ItemTaller(BaseModel):
    id_taller:            int
    razon_social:         str
    estado_registro:      str
    total_servicios:      int
    servicios_completados: int
    ingresos_taller:      Decimal


class ReporteTalleres(BaseModel):
    items:          List[ItemTaller]
    total:          int
    total_ingresos: Decimal


# ── Pagos ─────────────────────────────────────────────────────────────────────

class ItemPago(BaseModel):
    id_pago:             int
    id_incidente:        int
    metodo_pago:         str
    monto_total:         Decimal
    monto_taller:        Decimal
    comision_plataforma: Decimal
    estado:              str
    referencia:          Optional[str]
    created_at:          datetime

    model_config = {"from_attributes": True}


class ReportePagos(BaseModel):
    items:          List[ItemPago]
    total:          int
    monto_total:    Decimal
    comision_total: Decimal
    por_metodo:     Dict[str, int]
    por_estado:     Dict[str, int]
