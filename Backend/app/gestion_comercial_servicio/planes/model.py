from datetime import datetime
from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, ForeignKey,
    Integer, Numeric, String, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import relationship
from app.database import Base


class Plan(Base):
    __tablename__ = "planes"

    id_plan        = Column(BigInteger, primary_key=True, autoincrement=True)
    slug           = Column(String(60), unique=True, nullable=False)
    nombre         = Column(String(100), nullable=False)
    descripcion    = Column(Text, nullable=True)
    precio         = Column(Numeric(10, 2), nullable=False, default=0)
    moneda         = Column(String(10), nullable=False, default="BOB")

    # Límites operativos (0 = sin límite)
    max_incidentes_mes = Column(Integer, nullable=False, default=0)
    max_tecnicos       = Column(Integer, nullable=False, default=0)
    max_usuarios       = Column(Integer, nullable=False, default=0)

    # Características
    tiene_ia                  = Column(Boolean, nullable=False, default=False)
    tiene_reportes_avanzados  = Column(Boolean, nullable=False, default=False)
    tiene_soporte_prioritario = Column(Boolean, nullable=False, default=False)
    tiene_notificaciones_push = Column(Boolean, nullable=False, default=True)

    orden  = Column(Integer, nullable=False, default=0)
    estado = Column(String(20), nullable=False, default="ACTIVO")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class TenantSuscripcion(Base):
    __tablename__ = "tenant_suscripciones"

    id_suscripcion = Column(BigInteger, primary_key=True, autoincrement=True)
    id_tenant      = Column(BigInteger, ForeignKey("tenants.id_tenant", ondelete="CASCADE"), nullable=False)
    id_plan        = Column(BigInteger, ForeignKey("planes.id_plan"), nullable=False)

    estado         = Column(String(20), nullable=False, default="ACTIVO")  # ACTIVO | CANCELADO | VENCIDO
    es_trial       = Column(Boolean, nullable=False, default=False)
    fecha_inicio   = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    fecha_fin      = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    plan = relationship("Plan", lazy="raise")

    __table_args__ = (
        UniqueConstraint("id_tenant", "estado", name="uq_tenant_suscripcion_activa"),
    )
