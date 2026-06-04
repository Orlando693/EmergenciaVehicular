from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Index, Integer, Numeric, String, func
from sqlalchemy.orm import relationship

from app.database import Base


class PagoGatewayTransaccion(Base):
    """
    CU23 - Historial de intentos de pago contra la pasarela externa.

    Cada llamada al gateway genera un registro; permite:
    - Reintentos ante rechazo (múltiples filas por id_pago).
    - Trazabilidad completa de cada intento (código, mensaje, referencia externa).
    - Soporte para estado PENDIENTE hasta recibir confirmación (webhook).

    Relación: muchos PagoGatewayTransaccion → un Pago.
    """

    __tablename__ = "pago_gateway_transacciones"
    __table_args__ = (
        Index("ix_pgt_tenant_pago", "id_tenant", "id_pago"),
    )

    id_transaccion = Column(BigInteger, primary_key=True, autoincrement=True)
    id_tenant      = Column(BigInteger, ForeignKey("tenants.id_tenant"), nullable=False)
    id_pago        = Column(BigInteger, ForeignKey("pagos.id_pago", ondelete="CASCADE"), nullable=False)

    # Datos enviados al gateway
    gateway_nombre = Column(String(50),  nullable=False, default="PASARELA_SANDBOX")
    metodo_pago    = Column(String(50),  nullable=False)
    monto          = Column(Numeric(10, 2), nullable=False)
    intento_numero = Column(Integer, nullable=False, default=1)

    # Respuesta recibida del gateway
    gateway_referencia = Column(String(200), nullable=True)   # ID de la transacción externa
    gateway_codigo     = Column(String(50),  nullable=True)   # código de respuesta
    gateway_mensaje    = Column(String(500), nullable=True)   # descripción de la respuesta
    estado             = Column(String(30),  nullable=False, default="PENDIENTE")
    # APROBADO | RECHAZADO | PENDIENTE | ERROR_CONEXION

    created_at = Column(DateTime, nullable=False, default=func.now())

    tenant = relationship("Tenant")
    pago   = relationship("Pago")
