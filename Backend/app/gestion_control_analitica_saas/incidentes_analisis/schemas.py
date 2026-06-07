from pydantic import BaseModel


class ItemConteo(BaseModel):
    nombre: str
    total:  int
    pct:    float   # porcentaje respecto al total global


class ZonaItem(BaseModel):
    zona:    str
    total:   int
    pct:     float


class TendenciaDia(BaseModel):
    fecha:  str   # "YYYY-MM-DD"
    total:  int


class IncidentesAnalisisOut(BaseModel):
    # Totales por estado (tarjetas)
    total:          int
    por_estado:     list[ItemConteo]   # REPORTADO, ASIGNADO, EN_CAMINO, …

    # Por tipo / clasificación IA
    por_tipo:       list[ItemConteo]

    # Por zona (top 10 por dirección)
    por_zona:       list[ZonaItem]

    # Tendencia diaria (últimos N días)
    tendencia:      list[TendenciaDia]

    # Cruce tipo × estado (top tipos y sus estados)
    cruce_tipo_estado: list[dict]   # {tipo, estados: {estado: count}}
