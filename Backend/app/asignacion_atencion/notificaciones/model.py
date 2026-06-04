from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.database import Base


class Notificacion(Base):
    __tablename__ = "notificaciones"

    id_notificacion = Column(BigInteger, primary_key=True, autoincrement=True)
    id_tenant       = Column(BigInteger, ForeignKey("tenants.id_tenant"), nullable=False)
    id_usuario      = Column(BigInteger, ForeignKey("usuarios.id_usuario", ondelete="CASCADE"), nullable=False)
    id_incidente    = Column(BigInteger, ForeignKey("incidentes.id_incidente", ondelete="CASCADE"), nullable=True)

    titulo  = Column(String(200), nullable=False)
    mensaje = Column(String(600), nullable=False)
    tipo    = Column(String(50),  nullable=False, default="INFO")

    leida      = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=func.now())

    usuario   = relationship("Usuario")
    tenant    = relationship("Tenant")
    incidente = relationship("Incidente")


class DispositivoPush(Base):
    __tablename__ = "dispositivos_push"
    __table_args__ = (UniqueConstraint("fcm_token", name="uq_dispositivos_push_fcm_token"),)

    id_dispositivo = Column(BigInteger, primary_key=True, autoincrement=True)
    id_tenant  = Column(BigInteger, ForeignKey("tenants.id_tenant"), nullable=False)
    id_usuario = Column(BigInteger, ForeignKey("usuarios.id_usuario", ondelete="CASCADE"), nullable=False)
    fcm_token  = Column(String(512), nullable=False)
    platform   = Column(String(40), nullable=True)
    activo     = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    usuario = relationship("Usuario")
    tenant  = relationship("Tenant")
