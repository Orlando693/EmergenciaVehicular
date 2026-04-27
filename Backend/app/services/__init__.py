
from app.services.general import auth_service
from app.services.administracion import usuario_service, rol_service
from app.services.operaciones import taller_service, tecnico_service
from app.services.gestion_vehiculos import vehiculo_service
from app.services.gestion_incidentes import incidente_service
from app.services.asignacion_atencion import (
    asignacion_service,
    chat_service,
    notificacion_service,
    firebase_push_service,
)
from app.services.gestion_servicios import pago_service
from app.services.bitacora_reportes import bitacora_service, reporte_service
