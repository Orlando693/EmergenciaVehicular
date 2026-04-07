from sqlalchemy import (
    BigInteger, Boolean, Column, ForeignKey, Numeric,
    String, DateTime, Enum as SAEnum, func,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.enums import EstadoTecnicoEnum


class Tecnico(Base):
    __tablename__ = "tecnicos"

    id_tecnico = Column(BigInteger, primary_key=True, autoincrement=True)
    id_taller = Column(BigInteger, ForeignKey("talleres.id_taller", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    nombres = Column(String(100), nullable=False)
    apellidos = Column(String(100), nullable=False)
    telefono = Column(String(30))
    especialidad = Column(String(120))
    latitud = Column(Numeric(10, 7))
    longitud = Column(Numeric(10, 7))
    estado = Column(SAEnum(EstadoTecnicoEnum, name="estado_tecnico_enum"), nullable=False, default=EstadoTecnicoEnum.DISPONIBLE)
    activo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    taller = relationship("Taller", back_populates="tecnicos")
