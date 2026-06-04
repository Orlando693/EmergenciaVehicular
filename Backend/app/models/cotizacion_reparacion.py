from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Index, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.database import Base


class CotizacionReparacion(Base):
    __tablename__ = "cotizaciones_reparacion"
    __table_args__ = (
        UniqueConstraint("id_tenant", "id_incidente", "id_taller", name="uq_cotizacion_tenant_incidente_taller"),
        Index("ix_cotizaciones_tenant_cliente", "id_tenant", "id_cliente"),
        Index("ix_cotizaciones_tenant_taller", "id_tenant", "id_taller"),
        Index("ix_cotizaciones_tenant_incidente", "id_tenant", "id_incidente"),
    )

    id_cotizacion = Column(BigInteger, primary_key=True, autoincrement=True)
    id_tenant = Column(BigInteger, ForeignKey("tenants.id_tenant"), nullable=False)
    id_incidente = Column(BigInteger, ForeignKey("incidentes.id_incidente", ondelete="CASCADE"), nullable=False)
    id_cliente = Column(BigInteger, ForeignKey("clientes.id_cliente", ondelete="CASCADE"), nullable=False)
    id_taller = Column(BigInteger, ForeignKey("talleres.id_taller", ondelete="CASCADE"), nullable=False)

    descripcion_solicitud = Column(String(500), nullable=True)
    estado = Column(String(30), nullable=False, default="PENDIENTE")
    precio_estimado = Column(Numeric(12, 2), nullable=True)
    detalle_danio = Column(String(1000), nullable=True)
    condiciones_servicio = Column(String(1000), nullable=True)
    tiempo_estimado = Column(String(100), nullable=True)
    respuesta_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    tenant = relationship("Tenant")
    incidente = relationship("Incidente")
    cliente = relationship("Cliente")
    taller = relationship("Taller")
