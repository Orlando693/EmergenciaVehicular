from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.database import Base


class EstimacionAtencion(Base):
    """
    CU22 - Gestionar estimación de atención y reparación.

    Una sola estimación vigente por incidente (constraint UNIQUE id_tenant + id_incidente).
    Los cambios se trazabilizan mediante bitácora e incidente_historial.
    """

    __tablename__ = "estimaciones_atencion"
    __table_args__ = (
        UniqueConstraint(
            "id_tenant", "id_incidente",
            name="uq_estimacion_tenant_incidente",
        ),
    )

    id_estimacion = Column(BigInteger, primary_key=True, autoincrement=True)
    id_tenant     = Column(BigInteger, ForeignKey("tenants.id_tenant"), nullable=False)
    id_incidente  = Column(BigInteger, ForeignKey("incidentes.id_incidente", ondelete="CASCADE"), nullable=False)
    id_taller     = Column(BigInteger, ForeignKey("talleres.id_taller",    ondelete="CASCADE"), nullable=False)

    # Tiempo estimado de llegada: texto libre ("15 minutos", "~30 min", etc.)
    tiempo_llegada = Column(String(150), nullable=True)
    # Tiempo estimado de reparación
    tiempo_reparacion = Column(String(150), nullable=True)
    # Observaciones adicionales del taller sobre el servicio
    observacion = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    tenant    = relationship("Tenant")
    incidente = relationship("Incidente")
    taller    = relationship("Taller")
