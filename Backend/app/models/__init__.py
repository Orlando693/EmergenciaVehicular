"""
Hub de re-exportación de modelos SQLAlchemy.
Garantiza que todos los modelos queden registrados en Base.metadata
para que Alembic y create_all() los detecten correctamente.
"""
from app.administracion.tenants.model import Tenant
from app.administracion.usuarios.model import Usuario, Rol, Permiso, RolPermiso, UsuarioRol, Cliente
from app.operaciones.talleres.model import Taller
from app.operaciones.tecnicos.model import Tecnico
from app.gestion_vehiculos.vehiculos.model import Vehiculo
from app.gestion_incidentes.incidentes.model import Incidente, IncidenteHistorial
from app.bitacora_reportes.bitacora.model import Bitacora
from app.bitacora_reportes.backup.model import BackupRegistro, BackupConfig
from app.asignacion_atencion.notificaciones.model import Notificacion, DispositivoPush
from app.asignacion_atencion.chat.model import MensajeChat
from app.gestion_servicios.pagos.model import Pago
from app.gestion_operativa_atencion.sincronizacion_offline.model import EmergenciaOfflineSync
from app.gestion_operativa_atencion.cotizaciones.model import CotizacionReparacion
from app.gestion_operativa_atencion.gestionar_atencion_reparacion.model import EstimacionAtencion
from app.gestion_comercial_servicio.procesar_pago_pasarela.model import PagoGatewayTransaccion
from app.gestion_comercial_servicio.planes.model import Plan, TenantSuscripcion
from app.plataform_superAdmin.model import SuperAdmin

__all__ = [
    "Tenant",
    "Usuario", "Rol", "Permiso", "RolPermiso", "UsuarioRol", "Cliente",
    "Taller", "Tecnico", "Vehiculo",
    "Incidente", "IncidenteHistorial",
    "Bitacora", "Notificacion", "DispositivoPush", "MensajeChat", "Pago",
    "EmergenciaOfflineSync", "CotizacionReparacion",
    "EstimacionAtencion",
    "PagoGatewayTransaccion",
    "Plan", "TenantSuscripcion",
    "SuperAdmin",
]
