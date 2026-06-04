"""
CU21 - Seleccionar taller para el servicio

No requiere tabla propia. La selección se registra actualizando:
  - cotizaciones_reparacion.estado → ACEPTADA / RECHAZADA
  - incidentes.id_taller           → taller elegido
  - incidentes.estado              → EN_PROCESO

Modelos externos utilizados:
  - CotizacionReparacion  (gestion_operativa_atencion.cotizaciones)
  - Incidente             (gestion_incidentes.incidentes)
  - Taller                (operaciones.talleres)
  - Cliente               (administracion.usuarios)
  - Bitacora              (bitacora_reportes.bitacora)
"""
from app.gestion_operativa_atencion.cotizaciones.model import CotizacionReparacion
from app.gestion_incidentes.incidentes.model import Incidente, IncidenteHistorial
from app.operaciones.talleres.model import Taller
from app.administracion.usuarios.model import Cliente
from app.bitacora_reportes.bitacora.model import Bitacora

__all__ = [
    "CotizacionReparacion",
    "Incidente",
    "IncidenteHistorial",
    "Taller",
    "Cliente",
    "Bitacora",
]
