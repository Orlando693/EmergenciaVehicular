from sqlalchemy import BigInteger, Boolean, Column, DateTime, String, func

from app.database import Base


class SuperAdmin(Base):
    __tablename__ = "super_admins"

    id_superadmin = Column(BigInteger, primary_key=True, autoincrement=True)
    email         = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    nombre        = Column(String(100), nullable=False, default="SuperAdmin")
    activo        = Column(Boolean, nullable=False, default=True)
    created_at    = Column(DateTime, nullable=False, default=func.now())
    updated_at    = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
