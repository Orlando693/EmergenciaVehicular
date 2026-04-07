from app.models.usuario import Usuario, Rol, Permiso, RolPermiso, UsuarioRol
from app.models.cliente import Cliente
from app.models.taller import Taller
from app.models.tecnico import Tecnico
from app.models.vehiculo import Vehiculo

__all__ = [
    "Usuario", "Rol", "Permiso", "RolPermiso", "UsuarioRol",
    "Cliente", "Taller", "Tecnico", "Vehiculo",
]
