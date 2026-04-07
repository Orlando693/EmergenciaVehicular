from fastapi import APIRouter, Depends

from app.core.dependencies import DBDep, CurrentUser, require_roles
from app.schemas.tecnico import TecnicoCreate, TecnicoUpdate, TecnicoOut
from app.services import tecnico_service, taller_service

router = APIRouter(prefix="/talleres/{id_taller}/tecnicos", tags=["Técnicos (CU9)"])


@router.post("", response_model=TecnicoOut, status_code=201, summary="CU9 - Registrar técnico")
async def crear_tecnico(
    id_taller: int,
    data: TecnicoCreate,
    current_user: CurrentUser,
    db: DBDep,
):
    """El dueño del taller registra un técnico."""
    taller = await taller_service.obtener_taller_por_usuario(current_user.id_usuario, db)
    if taller.id_taller != id_taller:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="No tienes permiso sobre este taller")
    return await tecnico_service.crear_tecnico(id_taller, data, db)


@router.get("", response_model=list[TecnicoOut], summary="CU9 - Listar técnicos del taller")
async def listar_tecnicos(id_taller: int, current_user: CurrentUser, db: DBDep):
    return await tecnico_service.listar_tecnicos(id_taller, db)


@router.get("/{id_tecnico}", response_model=TecnicoOut, summary="Obtener técnico")
async def obtener_tecnico(id_taller: int, id_tecnico: int, db: DBDep, current_user: CurrentUser):
    return await tecnico_service.obtener_tecnico(id_tecnico, db)


@router.put("/{id_tecnico}", response_model=TecnicoOut, summary="CU9 - Actualizar técnico")
async def actualizar_tecnico(
    id_taller: int,
    id_tecnico: int,
    data: TecnicoUpdate,
    current_user: CurrentUser,
    db: DBDep,
):
    taller = await taller_service.obtener_taller_por_usuario(current_user.id_usuario, db)
    if taller.id_taller != id_taller:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="No tienes permiso sobre este taller")
    return await tecnico_service.actualizar_tecnico(id_tecnico, data, db)


@router.delete("/{id_tecnico}", summary="CU9 - Desactivar técnico")
async def eliminar_tecnico(
    id_taller: int,
    id_tecnico: int,
    current_user: CurrentUser,
    db: DBDep,
):
    taller = await taller_service.obtener_taller_por_usuario(current_user.id_usuario, db)
    if taller.id_taller != id_taller:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="No tienes permiso sobre este taller")
    return await tecnico_service.eliminar_tecnico(id_tecnico, db)
