from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import DBDep, CurrentUser, require_roles
from app.operaciones.tecnicos.schemas import TecnicoCreate, TecnicoUpdate, TecnicoOut
from app.operaciones.tecnicos import service as tecnico_service
from app.operaciones.talleres import service as taller_service

# Router para ADMIN: lista todos los técnicos del tenant
router = APIRouter(prefix="/tecnicos", tags=["Técnicos (CU9)"])


@router.get(
    "",
    response_model=list[TecnicoOut],
    summary="ADMIN - Listar todos los técnicos del tenant",
    dependencies=[Depends(require_roles("ADMINISTRADOR"))],
)
async def listar_todos_tecnicos(current_user: CurrentUser, db: DBDep):
    """El administrador visualiza todos los técnicos registrados en el tenant."""
    return await tecnico_service.listar_todos_tecnicos(current_user.id_tenant, db)


# Router anidado bajo /talleres/{id_taller}/tecnicos para operaciones del TALLER
taller_tecnicos_router = APIRouter(
    prefix="/talleres/{id_taller}/tecnicos",
    tags=["Técnicos (CU9)"],
)


@taller_tecnicos_router.post("", response_model=TecnicoOut, status_code=201, summary="CU9 - Registrar técnico")
async def crear_tecnico(
    id_taller: int,
    data: TecnicoCreate,
    current_user: CurrentUser,
    db: DBDep,
):
    """El dueño del taller registra un técnico."""
    taller = await taller_service.obtener_taller_por_usuario(current_user.id_usuario, db, current_user.id_tenant)
    if taller.id_taller != id_taller:
        raise HTTPException(status_code=403, detail="No tienes permiso sobre este taller")
    return await tecnico_service.crear_tecnico(id_taller, current_user.id_tenant, data, db)


@taller_tecnicos_router.get("", response_model=list[TecnicoOut], summary="CU9 - Listar técnicos del taller")
async def listar_tecnicos(id_taller: int, current_user: CurrentUser, db: DBDep):
    return await tecnico_service.listar_tecnicos(id_taller, current_user.id_tenant, db)


@taller_tecnicos_router.get("/{id_tecnico}", response_model=TecnicoOut, summary="Obtener técnico")
async def obtener_tecnico(id_taller: int, id_tecnico: int, db: DBDep, current_user: CurrentUser):
    return await tecnico_service.obtener_tecnico(id_tecnico, id_taller, current_user.id_tenant, db)


@taller_tecnicos_router.put("/{id_tecnico}", response_model=TecnicoOut, summary="CU9 - Actualizar técnico")
async def actualizar_tecnico(
    id_taller: int,
    id_tecnico: int,
    data: TecnicoUpdate,
    current_user: CurrentUser,
    db: DBDep,
):
    taller = await taller_service.obtener_taller_por_usuario(current_user.id_usuario, db, current_user.id_tenant)
    if taller.id_taller != id_taller:
        raise HTTPException(status_code=403, detail="No tienes permiso sobre este taller")
    return await tecnico_service.actualizar_tecnico(id_tecnico, id_taller, current_user.id_tenant, data, db)


@taller_tecnicos_router.delete("/{id_tecnico}", summary="CU9 - Desactivar técnico")
async def eliminar_tecnico(
    id_taller: int,
    id_tecnico: int,
    current_user: CurrentUser,
    db: DBDep,
):
    taller = await taller_service.obtener_taller_por_usuario(current_user.id_usuario, db, current_user.id_tenant)
    if taller.id_taller != id_taller:
        raise HTTPException(status_code=403, detail="No tienes permiso sobre este taller")
    return await tecnico_service.eliminar_tecnico(id_tecnico, id_taller, current_user.id_tenant, db)
