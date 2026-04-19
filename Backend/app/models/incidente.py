from sqlalchemy import BigInteger, Column, String, DateTime, func, Float, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Incidente(Base):
    __tablename__ = "incidentes"

    id_incidente = Column(BigInteger, primary_key=True, autoincrement=True)
    id_cliente = Column(BigInteger, ForeignKey("clientes.id_cliente", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    id_vehiculo = Column(BigInteger, ForeignKey("vehiculos.id_vehiculo", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    id_taller = Column(BigInteger, ForeignKey("talleres.id_taller", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    
    descripcion = Column(String(1000), nullable=False)
    audio_url = Column(String(255), nullable=True)
    imagen_url = Column(String(255), nullable=True)
    resumen_ia = Column(String(1000), nullable=True)
    clasificacion_ia = Column(String(100), nullable=True)
    
    ubicacion_lat = Column(Float, nullable=True)
    ubicacion_lng = Column(Float, nullable=True)
    direccion = Column(String(255), nullable=True)
    
    estado = Column(String(50), nullable=False, default="REPORTADO") # REPORTADO, EN_PROCESO, RESUELTO, CANCELADO
    
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    cliente = relationship("Cliente")
    vehiculo = relationship("Vehiculo")
    taller = relationship("Taller")
    historial = relationship("IncidenteHistorial", back_populates="incidente", cascade="all, delete-orphan", order_by="desc(IncidenteHistorial.created_at)")

class IncidenteHistorial(Base):
    __tablename__ = "incidente_historial"

    id_historial = Column(BigInteger, primary_key=True, autoincrement=True)
    id_incidente = Column(BigInteger, ForeignKey("incidentes.id_incidente", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    estado_anterior = Column(String(50), nullable=True)
    estado_nuevo = Column(String(50), nullable=False)
    observacion = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())

    incidente = relationship("Incidente", back_populates="historial")