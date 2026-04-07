from sqlalchemy import (
    BigInteger, Boolean, Column, ForeignKey, Integer, Numeric,
    String, DateTime, Enum as SAEnum, func,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.enums import EstadoTallerEnum


class Taller(Base):
    __tablename__ = "talleres"

    id_taller = Column(BigInteger, primary_key=True, autoincrement=True)
    id_usuario = Column(BigInteger, ForeignKey("usuarios.id_usuario", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, unique=True)
    razon_social = Column(String(150), nullable=False)
    nombre_comercial = Column(String(150), nullable=False)
    nit = Column(String(30), unique=True)
    telefono_atencion = Column(String(30))
    email_atencion = Column(String(150))
    direccion = Column(String(255), nullable=False)
    referencia = Column(String(255))
    latitud = Column(Numeric(10, 7))
    longitud = Column(Numeric(10, 7))
    capacidad_maxima = Column(Integer, nullable=False, default=1)
    acepta_remolque = Column(Boolean, nullable=False, default=False)
    estado_registro = Column(SAEnum(EstadoTallerEnum, name="estado_taller_enum"), nullable=False, default=EstadoTallerEnum.PENDIENTE)
    calificacion_promedio = Column(Numeric(3, 2))
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    usuario = relationship("Usuario", back_populates="taller")
    tecnicos = relationship("Tecnico", back_populates="taller", cascade="all, delete-orphan")
