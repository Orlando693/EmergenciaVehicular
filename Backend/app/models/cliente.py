from sqlalchemy import BigInteger, Column, ForeignKey, String, DateTime, func
from sqlalchemy.orm import relationship

from app.database import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id_cliente = Column(BigInteger, primary_key=True, autoincrement=True)
    id_usuario = Column(BigInteger, ForeignKey("usuarios.id_usuario", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, unique=True)
    ci = Column(String(30))
    direccion = Column(String(255))
    referencia = Column(String(255))
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    usuario = relationship("Usuario", back_populates="cliente")
    vehiculos = relationship("Vehiculo", back_populates="cliente")
