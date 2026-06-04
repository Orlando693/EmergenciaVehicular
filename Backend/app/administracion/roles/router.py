from fastapi import APIRouter, Depends

from app.core.dependencies import CurrentUser, DBDep, require_roles
from app.administracion.roles.schemas import RolCreate, RolUpdate, RolOut, PermisoOut, AsignarPermisoRequest, AsignarRolRequest, PermisoCreate
from app.administracion.roles import service as rol_service

router = APIRouter(prefix="/roles", tags=["Roles y Permisos (CU4)"],
                   dependencies=[Depends(require_roles("ADMINISTRADOR"))])


@router.get("", response_model=list[RolOut], summary="Listar roles (propios + sistema)")
async def listar_roles(db: DBDep, current_user: CurrentUser):
    return await rol_service.listar_roles(db, current_user.id_tenant)


@router.post("", response_model=RolOut, status_code=201, summary="Crear rol para mi tenant")
async def crear_rol(data: RolCreate, db: DBDep, current_user: CurrentUser):
    return await rol_service.crear_rol(data, db, current_user.id_tenant)


@router.put("/{id_rol}", response_model=RolOut, summary="Actualizar rol (solo propios)")
async def actualizar_rol(id_rol: int, data: RolUpdate, db: DBDep, current_user: CurrentUser):
    return await rol_service.actualizar_rol(id_rol, data, db, current_user.id_tenant)


@router.delete("/{id_rol}", summary="Eliminar rol (solo propios)")
async def eliminar_rol(id_rol: int, db: DBDep, current_user: CurrentUser):
    return await rol_service.eliminar_rol(id_rol, db, current_user.id_tenant)


@router.put("/{id_rol}/permisos", response_model=RolOut, summary="Asignar permisos a rol")
async def asignar_permisos(id_rol: int, data: AsignarPermisoRequest, db: DBDep):
    return await rol_service.asignar_permisos_a_rol(id_rol, data.id_permisos, db)


@router.get("/permisos", response_model=list[PermisoOut], summary="Listar permisos")
async def listar_permisos(db: DBDep):
    return await rol_service.listar_permisos(db)


@router.post("/permisos", response_model=PermisoOut, status_code=201, summary="Crear permiso")
async def crear_permiso(data: PermisoCreate, db: DBDep):
    return await rol_service.crear_permiso(data, db)


@router.put("/usuarios/{id_usuario}/roles", summary="Asignar roles a usuario")
async def asignar_roles_usuario(id_usuario: int, data: AsignarRolRequest, db: DBDep, current_user: CurrentUser):
    return await rol_service.asignar_roles_a_usuario(id_usuario, data.id_roles, db, current_user.id_tenant)
