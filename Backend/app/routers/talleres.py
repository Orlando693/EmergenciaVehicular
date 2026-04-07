from fastapi import APIRouter, Depends, Query

from app.core.dependencies import DBDep, CurrentUser, require_roles
from app.models.enums import EstadoTallerEnum
from app.schemas.taller import TallerCreate, TallerUpdate, TallerOut, TallerEstadoUpdate
from app.services import taller_service

router = APIRouter(prefix="/talleres", tags=["Talleres (CU7, CU8)"])


@router.post("", response_model=TallerOut, status_code=201, summary="CU7 - Registrar taller")
async def registrar_taller(
    data: TallerCreate,
    current_user: CurrentUser,
    db: DBDep,
):
    """El usuario autenticado registra su taller. Estado inicial: PENDIENTE."""
    return await taller_service.registrar_taller(current_user.id_usuario, data, db)


@router.get("", response_model=list[TallerOut], summary="Listar talleres",
            dependencies=[Depends(require_roles("ADMINISTRADOR", "TALLER", "CLIENTE"))])
async def listar_talleres(
    db: DBDep,
    estado: EstadoTallerEnum | None = Query(None, description="Filtrar por estado"),
):
    return await taller_service.listar_talleres(db, estado)


@router.get("/mi-taller", response_model=TallerOut, summary="CU8 - Ver mi taller")
async def mi_taller(current_user: CurrentUser, db: DBDep):
    """El usuario TALLER consulta su propio perfil de taller."""
    return await taller_service.obtener_taller_por_usuario(current_user.id_usuario, db)


@router.put("/mi-taller", response_model=TallerOut, summary="CU8 - Actualizar mi taller")
async def actualizar_mi_taller(
    data: TallerUpdate,
    current_user: CurrentUser,
    db: DBDep,
):
    taller = await taller_service.obtener_taller_por_usuario(current_user.id_usuario, db)
    return await taller_service.actualizar_taller(taller.id_taller, data, db)


@router.get("/{id_taller}", response_model=TallerOut, summary="Obtener taller por ID")
async def obtener_taller(id_taller: int, db: DBDep, current_user: CurrentUser):
    return await taller_service.obtener_taller(id_taller, db)


@router.put("/{id_taller}", response_model=TallerOut, summary="Admin - Actualizar taller",
            dependencies=[Depends(require_roles("ADMINISTRADOR"))])
async def actualizar_taller(id_taller: int, data: TallerUpdate, db: DBDep):
    return await taller_service.actualizar_taller(id_taller, data, db)


@router.patch("/{id_taller}/estado", response_model=TallerOut,
              summary="Admin - Aprobar / Rechazar taller",
              dependencies=[Depends(require_roles("ADMINISTRADOR"))])
async def cambiar_estado_taller(id_taller: int, data: TallerEstadoUpdate, db: DBDep):
    """El administrador aprueba, rechaza o suspende un taller."""
    return await taller_service.cambiar_estado_taller(id_taller, data, db)
