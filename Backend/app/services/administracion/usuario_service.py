from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import hash_password, verify_password
from app.models.cliente import Cliente
from app.models.usuario import Rol, Usuario, UsuarioRol
from app.schemas.usuario import CambiarPasswordRequest, UsuarioCreate, UsuarioOut, UsuarioUpdate
from app.services.administracion.tenant_service import obtener_tenant_demo


async def _get_rol_or_404(nombre: str, db: AsyncSession) -> Rol:
    result = await db.execute(select(Rol).where(Rol.nombre == nombre, Rol.activo == True))
    rol = result.scalar_one_or_none()
    if not rol:
        raise HTTPException(status_code=400, detail=f"Rol '{nombre}' no existe o esta inactivo")
    return rol


async def registrar_usuario(data: UsuarioCreate, db: AsyncSession, id_tenant: int | None = None) -> UsuarioOut:
    existe = await db.execute(select(Usuario).where(func.lower(Usuario.email) == data.email.lower()))
    if existe.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="El email ya esta registrado")

    if id_tenant is None:
        tenant = await obtener_tenant_demo(db)
        id_tenant = tenant.id_tenant

    rol = await _get_rol_or_404(data.rol.upper(), db)

    nuevo = Usuario(
        id_tenant=id_tenant,
        nombres=data.nombres,
        apellidos=data.apellidos,
        email=data.email,
        telefono=data.telefono,
        password_hash=hash_password(data.password),
    )
    db.add(nuevo)
    await db.flush()

    db.add(UsuarioRol(id_usuario=nuevo.id_usuario, id_rol=rol.id_rol))

    if data.rol.upper() == "CLIENTE":
        db.add(Cliente(id_tenant=id_tenant, id_usuario=nuevo.id_usuario))

    await db.commit()
    await db.refresh(nuevo, ["roles"])
    return UsuarioOut.from_orm_with_roles(nuevo)


async def listar_usuarios(db: AsyncSession, id_tenant: int) -> list[UsuarioOut]:
    result = await db.execute(
        select(Usuario)
        .where(Usuario.id_tenant == id_tenant)
        .options(selectinload(Usuario.roles))
    )
    usuarios = result.scalars().all()
    return [UsuarioOut.from_orm_with_roles(u) for u in usuarios]


async def obtener_usuario(id_usuario: int, db: AsyncSession, id_tenant: int) -> UsuarioOut:
    result = await db.execute(
        select(Usuario)
        .where(Usuario.id_usuario == id_usuario, Usuario.id_tenant == id_tenant)
        .options(selectinload(Usuario.roles))
    )
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return UsuarioOut.from_orm_with_roles(usuario)


async def actualizar_perfil(
    id_usuario: int,
    data: UsuarioUpdate,
    db: AsyncSession,
    id_tenant: int | None = None,
) -> UsuarioOut:
    condiciones = [Usuario.id_usuario == id_usuario]
    if id_tenant is not None:
        condiciones.append(Usuario.id_tenant == id_tenant)

    result = await db.execute(
        select(Usuario)
        .where(*condiciones)
        .options(selectinload(Usuario.roles))
    )
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(usuario, field, value)

    await db.commit()
    await db.refresh(usuario, ["roles"])
    return UsuarioOut.from_orm_with_roles(usuario)


async def cambiar_password(
    id_usuario: int,
    data: CambiarPasswordRequest,
    db: AsyncSession,
    id_tenant: int | None = None,
) -> dict:
    condiciones = [Usuario.id_usuario == id_usuario]
    if id_tenant is not None:
        condiciones.append(Usuario.id_tenant == id_tenant)

    result = await db.execute(select(Usuario).where(*condiciones))
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if not verify_password(data.password_actual, usuario.password_hash):
        raise HTTPException(status_code=400, detail="La contrasena actual es incorrecta")

    usuario.password_hash = hash_password(data.password_nuevo)
    await db.commit()
    return {"detail": "Contrasena actualizada correctamente"}


async def cambiar_estado(id_usuario: int, estado: str, db: AsyncSession, id_tenant: int) -> UsuarioOut:
    result = await db.execute(
        select(Usuario)
        .where(Usuario.id_usuario == id_usuario, Usuario.id_tenant == id_tenant)
        .options(selectinload(Usuario.roles))
    )
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    usuario.estado = estado
    await db.commit()
    await db.refresh(usuario, ["roles"])
    return UsuarioOut.from_orm_with_roles(usuario)
