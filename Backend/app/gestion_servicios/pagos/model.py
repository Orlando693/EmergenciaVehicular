from sqlalchemy import BigInteger, Column, ForeignKey, Numeric, String, DateTime, func
from sqlalchemy.orm import relationship

from app.database import Base


class Pago(Base):
    __tablename__ = "pagos"

    id_pago      = Column(BigInteger, primary_key=True, autoincrement=True)
    id_tenant    = Column(BigInteger, ForeignKey("tenants.id_tenant"), nullable=False)
    id_incidente = Column(BigInteger, ForeignKey("incidentes.id_incidente", ondelete="CASCADE"), nullable=False, unique=True)
    id_cliente   = Column(BigInteger, ForeignKey("clientes.id_cliente", ondelete="CASCADE"), nullable=False)

    monto_total         = Column(Numeric(10, 2), nullable=False)
    monto_taller        = Column(Numeric(10, 2), nullable=False)
    comision_plataforma = Column(Numeric(10, 2), nullable=False)

    metodo_pago = Column(String(50), nullable=False)
    estado      = Column(String(30), nullable=False, default="PENDIENTE")

    referencia        = Column(String(100), nullable=True)
    descripcion_error = Column(String(300), nullable=True)

    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    incidente = relationship("Incidente")
    tenant    = relationship("Tenant")
    cliente   = relationship("Cliente")
