"""Normaliza el campo estado (Enum SQLAlchemy o str desde PostgreSQL)."""


def texto_estado_usuario(estado) -> str:
    if estado is None:
        return ""
    if isinstance(estado, str):
        return estado
    v = getattr(estado, "value", None)
    if v is not None:
        return str(v)
    return str(estado)
