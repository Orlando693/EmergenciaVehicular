from sqlalchemy import BigInteger, Boolean, Column, ForeignKey, String, DateTime, func
from sqlalchemy.orm import relationship

from app.database import Base


class Notificacion(Base):
    __tablename__ = "notificaciones"

    id_notificacion = Column(BigInteger, primary_key=True, autoincrement=True)
    id_usuario      = Column(BigInteger, ForeignKey("usuarios.id_usuario", ondelete="CASCADE"), nullable=False)
    id_incidente    = Column(BigInteger, ForeignKey("incidentes.id_incidente", ondelete="CASCADE"), nullable=True)

    titulo  = Column(String(200), nullable=False)
    mensaje = Column(String(600), nullable=False)
    tipo    = Column(String(50),  nullable=False, default="INFO")
    # NUEVO_INCIDENTE | ASIGNACION | ESTADO_CAMBIO | NUEVO_SERVICIO | INFO

    leida      = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=func.now())

    usuario   = relationship("Usuario")
    incidente = relationship("Incidente")
