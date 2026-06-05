from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, String, Text, func

from app.database import Base


class BackupRegistro(Base):
    __tablename__ = "backup_registros"

    id_backup    = Column(BigInteger, primary_key=True, autoincrement=True)
    id_tenant    = Column(BigInteger, ForeignKey("tenants.id_tenant"), nullable=False)
    id_usuario   = Column(BigInteger, ForeignKey("usuarios.id_usuario", ondelete="SET NULL"), nullable=True)
    tipo         = Column(String(20),  nullable=False, default="MANUAL")   # MANUAL | AUTOMATICO
    estado       = Column(String(20),  nullable=False, default="COMPLETADO")  # COMPLETADO | FALLIDO
    nombre_archivo = Column(String(255))
    tamano_bytes = Column(BigInteger, default=0)
    datos_json   = Column(Text)
    created_at   = Column(DateTime, nullable=False, default=func.now())


class BackupConfig(Base):
    __tablename__ = "backup_config"

    id_config    = Column(BigInteger, primary_key=True, autoincrement=True)
    id_tenant    = Column(BigInteger, ForeignKey("tenants.id_tenant"), nullable=False, unique=True)
    activo       = Column(Boolean, nullable=False, default=False)
    frecuencia   = Column(String(20), default="DIARIO")   # DIARIO | SEMANAL | MENSUAL
    hora         = Column(String(5),  default="02:00")    # "HH:MM"
    proximo_backup = Column(DateTime, nullable=True)
    ultimo_backup  = Column(DateTime, nullable=True)
    updated_at   = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
