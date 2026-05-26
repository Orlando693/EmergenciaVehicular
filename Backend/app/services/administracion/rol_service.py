from fastapi import HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.usuario import Rol, Permiso, RolPermiso, Usuario, UsuarioRol
from app.schemas.rol import RolCreate, RolUpdate, RolOut, PermisoOut, PermisoCreate


async def listar_roles(db: AsyncSession) -> list[RolOut]:
    result = await db.execute(select(Rol).options(selectinload(Rol.permisos)))
    return result.scalars().all()


async def crear_rol(data: RolCreate, db: AsyncSession) -> RolOut:
    existe = await db.execute(select(Rol).where(Rol.nombre == data.nombre))
    if existe.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="El rol ya existe")
    rol = Rol(nombre=data.nombre.upper(), descripcion=data.descripcion)
    db.add(rol)
    await db.commit()
    await db.refresh(rol, ["permisos"])
    return rol


async def actualizar_rol(id_rol: int, data: RolUpdate, db: AsyncSession) -> RolOut:
    result = await db.execute(
        select(Rol).where(Rol.id_rol == id_rol).options(selectinload(Rol.permisos))
    )
    rol = result.scalar_one_or_none()
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(rol, field, value)
    await db.commit()
    await db.refresh(rol, ["permisos"])
    return rol


async def eliminar_rol(id_rol: int, db: AsyncSession) -> dict:
    result = await db.execute(select(Rol).where(Rol.id_rol == id_rol))
    rol = result.scalar_one_or_none()
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    await db.delete(rol)
    await db.commit()
    return {"detail": "Rol eliminado"}


async def listar_permisos(db: AsyncSession) -> list[PermisoOut]:
    result = await db.execute(select(Permiso))
    return result.scalars().all()


async def crear_permiso(data: PermisoCreate, db: AsyncSession) -> PermisoOut:
    existe = await db.execute(select(Permiso).where(Permiso.codigo == data.codigo))
    if existe.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="El permiso ya existe")
    permiso = Permiso(codigo=data.codigo, descripcion=data.descripcion)
    db.add(permiso)
    await db.commit()
    await db.refresh(permiso)
    return permiso


async def asignar_permisos_a_rol(id_rol: int, id_permisos: list[int], db: AsyncSession) -> RolOut:
    result = await db.execute(
        select(Rol).where(Rol.id_rol == id_rol).options(selectinload(Rol.permisos))
    )
    rol = result.scalar_one_or_none()
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")

    await db.execute(delete(RolPermiso).where(RolPermiso.id_rol == id_rol))

    for id_p in id_permisos:
        db.add(RolPermiso(id_rol=id_rol, id_permiso=id_p))

    await db.commit()
    await db.refresh(rol, ["permisos"])
    return rol


async def asignar_roles_a_usuario(id_usuario: int, id_roles: list[int], db: AsyncSession) -> dict:
    result = await db.execute(select(Usuario).where(Usuario.id_usuario == id_usuario))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    await db.execute(delete(UsuarioRol).where(UsuarioRol.id_usuario == id_usuario))

    for id_r in id_roles:
        db.add(UsuarioRol(id_usuario=id_usuario, id_rol=id_r))

    await db.commit()
    return {"detail": "Roles asignados correctamente"}
