from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.database import Base


class EmergenciaOfflineSync(Base):
    __tablename__ = "emergencias_offline_sync"
    __table_args__ = (
        UniqueConstraint("id_tenant", "id_cliente", "client_sync_id", name="uq_offline_sync_tenant_cliente_client"),
        Index("ix_offline_sync_tenant_cliente", "id_tenant", "id_cliente"),
        Index("ix_offline_sync_incidente", "id_incidente"),
    )

    id_sync        = Column(BigInteger, primary_key=True, autoincrement=True)
    id_tenant      = Column(BigInteger, ForeignKey("tenants.id_tenant"), nullable=False)
    id_cliente     = Column(BigInteger, ForeignKey("clientes.id_cliente", ondelete="CASCADE"), nullable=False)
    client_sync_id = Column(String(100), nullable=False)
    id_incidente   = Column(BigInteger, ForeignKey("incidentes.id_incidente", ondelete="SET NULL"), nullable=True)
    estado_sync    = Column(String(30), nullable=False, default="PENDIENTE")
    intentos       = Column(BigInteger, nullable=False, default=0)
    error_mensaje  = Column(String(500), nullable=True)
    created_at     = Column(DateTime, nullable=False, default=func.now())
    updated_at     = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    tenant    = relationship("Tenant")
    cliente   = relationship("Cliente")
    incidente = relationship("Incidente")
