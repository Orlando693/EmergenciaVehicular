from pydantic import BaseModel


class KpiCard(BaseModel):
    label:     str
    value:     int | float | str
    subtitulo: str | None = None
    tendencia: str | None = None   # "up" | "down" | "neutral"


class ItemConteo(BaseModel):
    nombre: str
    total:  int


class TallerMetrica(BaseModel):
    nombre:               str
    total_incidentes:     int
    completados:          int
    cancelados:           int
    tasa_cumplimiento:    float      # porcentaje 0-100


class TendenciaDia(BaseModel):
    fecha:  str    # YYYY-MM-DD
    total:  int


class DashboardOperacionalOut(BaseModel):
    # KPIs
    total_incidentes:         int
    incidentes_activos:       int
    incidentes_completados:   int
    incidentes_cancelados:    int
    total_talleres:           int
    total_tecnicos:           int
    total_clientes:           int
    ingresos_totales:         float
    cumplimiento_sla:         float        # porcentaje

    # Distribuciones
    por_estado:               list[ItemConteo]
    por_clasificacion:        list[ItemConteo]
    por_taller:               list[TallerMetrica]
    tendencia_7dias:          list[TendenciaDia]
