from sqlalchemy import BigInteger, Column, ForeignKey, String, DateTime, func
from sqlalchemy.orm import relationship

from app.database import Base

class Bitacora(Base):
    __tablename__ = "bitacora"

    id_bitacora = Column(BigInteger, primary_key=True, autoincrement=True)
    modulo = Column(String(100), nullable=False)
    accion = Column(String(255), nullable=False)
    ip = Column(String(50))
    rol = Column(String(50))
    usuario_email = Column(String(150))
    created_at = Column(DateTime, nullable=False, default=func.now())

    id_usuario = Column(BigInteger, ForeignKey("usuarios.id_usuario", ondelete="SET NULL"), nullable=True)
    usuario = relationship("Usuario")
