from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel


class IniciarPagoRequest(BaseModel):
    metodo_pago: str
    # Para tarjeta (mock, no se almacena):
    numero_tarjeta: Optional[str] = None
    nombre_titular: Optional[str] = None
    vencimiento:    Optional[str] = None
    cvv:            Optional[str] = None


class PagoOut(BaseModel):
    id_pago:             int
    id_incidente:        int
    id_cliente:          int
    monto_total:         Decimal
    monto_taller:        Decimal
    comision_plataforma: Decimal
    metodo_pago:         str
    estado:              str
    referencia:          Optional[str] = None
    descripcion_error:   Optional[str] = None
    created_at:          datetime
    updated_at:          datetime

    model_config = {"from_attributes": True}


class CostoEstimado(BaseModel):
    id_incidente:        int
    clasificacion_ia:    Optional[str]
    monto_total:         Decimal
    monto_taller:        Decimal
    comision_plataforma: Decimal
    pago_existente:      Optional[PagoOut] = None


class PagoPage(BaseModel):
    items: List[PagoOut]
    total: int
