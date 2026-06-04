from sqlalchemy import BigInteger, Column, ForeignKey, String, DateTime, func
from sqlalchemy.orm import relationship

from app.database import Base


class MensajeChat(Base):
    __tablename__ = "mensajes_chat"

    id_mensaje    = Column(BigInteger, primary_key=True, autoincrement=True)
    id_tenant     = Column(BigInteger, ForeignKey("tenants.id_tenant"), nullable=False)
    id_incidente  = Column(BigInteger, ForeignKey("incidentes.id_incidente", ondelete="CASCADE"), nullable=False, index=True)
    id_usuario    = Column(BigInteger, ForeignKey("usuarios.id_usuario", ondelete="SET NULL"), nullable=True)

    contenido     = Column(String(2000), nullable=False)
    nombre_emisor = Column(String(200), nullable=False)
    rol_emisor    = Column(String(50),  nullable=False)

    created_at    = Column(DateTime, nullable=False, default=func.now())

    incidente = relationship("Incidente")
    tenant    = relationship("Tenant")
    usuario   = relationship("Usuario")
