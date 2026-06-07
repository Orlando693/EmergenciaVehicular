from pydantic import BaseModel


class KpiTiempo(BaseModel):
    label:        str
    minutos:      float | None   # None = sin datos
    descripcion:  str


class TallerKpi(BaseModel):
    nombre:                   str
    total_asignados:          int
    total_completados:        int
    avg_minutos_resolucion:   float | None
    tasa_cumplimiento:        float     # 0-100


class SlaDetalle(BaseModel):
    nivel:        str        # "EXCELENTE" | "BUENO" | "REGULAR" | "BAJO"
    porcentaje:   float
    completados:  int
    total:        int
    objetivo:     float      # 80 %


class KpisAtencionOut(BaseModel):
    # Tiempos promedio
    tiempos:              list[KpiTiempo]

    # SLA
    sla:                  SlaDetalle

    # Tasa de asignación y abandono
    tasa_asignacion:      float    # % incidentes que llegaron a ASIGNADO
    tasa_abandono:        float    # % cancelados después de ser asignados

    # Eficiencia por taller
    talleres:             list[TallerKpi]

    # Totales del período
    total_incidentes:     int
    total_asignados:      int
    total_completados:    int
    total_cancelados:     int
