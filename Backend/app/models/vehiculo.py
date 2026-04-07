from sqlalchemy import BigInteger, Boolean, Column, ForeignKey, Integer, String, DateTime, func
from sqlalchemy.orm import relationship

from app.database import Base


class Vehiculo(Base):
    __tablename__ = "vehiculos"

    id_vehiculo = Column(BigInteger, primary_key=True, autoincrement=True)
    id_cliente = Column(BigInteger, ForeignKey("clientes.id_cliente", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    placa = Column(String(20), nullable=False, unique=True)
    marca = Column(String(80), nullable=False)
    modelo = Column(String(80), nullable=False)
    anio = Column(Integer)
    color = Column(String(50))
    tipo_vehiculo = Column(String(50))
    vin = Column(String(50))
    activo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    cliente = relationship("Cliente", back_populates="vehiculos")
