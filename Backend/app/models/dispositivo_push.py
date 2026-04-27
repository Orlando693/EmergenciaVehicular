from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.database import Base


class DispositivoPush(Base):
    __tablename__ = "dispositivos_push"
    __table_args__ = (UniqueConstraint("fcm_token", name="uq_dispositivos_push_fcm_token"),)

    id_dispositivo = Column(BigInteger, primary_key=True, autoincrement=True)
    id_usuario = Column(BigInteger, ForeignKey("usuarios.id_usuario", ondelete="CASCADE"), nullable=False)
    fcm_token = Column(String(512), nullable=False)
    platform = Column(String(40), nullable=True)
    activo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    usuario = relationship("Usuario")
