from datetime import datetime

from sqlalchemy import (
    BigInteger, Boolean, Column, ForeignKey, String, Text, Enum as SAEnum,
    DateTime, func,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.enums import EstadoUsuarioEnum


class Rol(Base):
    __tablename__ = "roles"

    id_rol = Column(BigInteger, primary_key=True, autoincrement=True)
    nombre = Column(String(50), nullable=False, unique=True)
    descripcion = Column(String(255))
    activo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    permisos = relationship("Permiso", secondary="rol_permiso", back_populates="roles")
    usuarios = relationship("Usuario", secondary="usuario_rol", back_populates="roles")


class Permiso(Base):
    __tablename__ = "permisos"

    id_permiso = Column(BigInteger, primary_key=True, autoincrement=True)
    codigo = Column(String(80), nullable=False, unique=True)
    descripcion = Column(String(255))
    created_at = Column(DateTime, nullable=False, default=func.now())

    roles = relationship("Rol", secondary="rol_permiso", back_populates="permisos")


class RolPermiso(Base):
    __tablename__ = "rol_permiso"

    id_rol = Column(BigInteger, ForeignKey("roles.id_rol", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    id_permiso = Column(BigInteger, ForeignKey("permisos.id_permiso", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)


class Usuario(Base):
    __tablename__ = "usuarios"

    id_usuario = Column(BigInteger, primary_key=True, autoincrement=True)
    nombres = Column(String(100), nullable=False)
    apellidos = Column(String(100), nullable=False)
    email = Column(String(150), nullable=False, unique=True)
    telefono = Column(String(30))
    password_hash = Column(Text, nullable=False)
    estado = Column(SAEnum(EstadoUsuarioEnum, name="estado_usuario_enum"), nullable=False, default=EstadoUsuarioEnum.ACTIVO)
    ultimo_acceso = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    roles = relationship("Rol", secondary="usuario_rol", back_populates="usuarios")
    cliente = relationship("Cliente", back_populates="usuario", uselist=False)
    taller = relationship("Taller", back_populates="usuario", uselist=False)


class UsuarioRol(Base):
    __tablename__ = "usuario_rol"

    id_usuario = Column(BigInteger, ForeignKey("usuarios.id_usuario", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    id_rol = Column(BigInteger, ForeignKey("roles.id_rol", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
