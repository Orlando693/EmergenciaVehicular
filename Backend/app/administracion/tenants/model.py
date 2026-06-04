from sqlalchemy import BigInteger, Column, DateTime, String, func

from app.database import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id_tenant = Column(BigInteger, primary_key=True, autoincrement=True)
    nombre = Column(String(150), nullable=False)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    estado = Column(String(30), nullable=False, default="ACTIVO")
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
