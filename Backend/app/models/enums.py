import enum


class EstadoUsuarioEnum(str, enum.Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"
    BLOQUEADO = "BLOQUEADO"


class EstadoTallerEnum(str, enum.Enum):
    PENDIENTE = "PENDIENTE"
    APROBADO = "APROBADO"
    SUSPENDIDO = "SUSPENDIDO"
    RECHAZADO = "RECHAZADO"


class EstadoTecnicoEnum(str, enum.Enum):
    DISPONIBLE = "DISPONIBLE"
    OCUPADO = "OCUPADO"
    INACTIVO = "INACTIVO"
