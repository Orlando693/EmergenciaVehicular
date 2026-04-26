from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.core.dependencies import DBDep, CurrentUser, require_roles
from app.models.enums import EstadoTallerEnum
from app.schemas.taller import TallerCreate, TallerUpdate, TallerOut, TallerEstadoUpdate
from app.schemas.incidente import IncidenteOut
from app.services import taller_service, incidente_service
from app.services.asignacion_service import aceptar_solicitud, rechazar_solicitud


class RechazoSolicitud(BaseModel):
    observacion: str | None = Field(None, max_length=500)


router = APIRouter(prefix="/talleres", tags=["Talleres (CU7, CU8, CU11)"])

@router.get(
    "/solicitudes-disponibles", 
    response_model=list[IncidenteOut], 
    summary="CU11 - Visualizar solicitudes disponibles",
    dependencies=[Depends(require_roles("TALLER"))]
)
async def visualizar_solicitudes_disponibles(
    current_user: CurrentUser,
    db: DBDep,
):
    """Permite al taller visualizar solicitudes de asistencia no asignadas."""
    return await incidente_service.consultar_solicitudes_disponibles(db)

@router.get(
    "/solicitudes-disponibles/{id_incidente}", 
    response_model=IncidenteOut, 
    summary="CU11 - Detalle de solicitud disponible",
    dependencies=[Depends(require_roles("TALLER"))]
)
async def detalle_solicitud_disponible(
    id_incidente: int,
    current_user: CurrentUser,
    db: DBDep,
):
    """Muestra información pormenorizada de una solicitud (incidente) disponible."""
    return await incidente_service.obtener_detalle_solicitud(id_incidente, db)


@router.post(
    "/solicitudes-disponibles/{id_incidente}/aceptar",
    response_model=IncidenteOut,
    summary="CU11 - Taller acepta una solicitud",
    dependencies=[Depends(require_roles("TALLER"))],
)
async def aceptar_solicitud_endpoint(
    id_incidente: int,
    current_user: CurrentUser,
    db: DBDep,
):
    """El taller acepta una solicitud disponible. La solicitud queda asignada a su taller
    y pasa al estado EN_PROCESO. Se registra historial y se notifica al cliente."""
    return await aceptar_solicitud(id_incidente, current_user.id_usuario, db)


@router.post(
    "/solicitudes-disponibles/{id_incidente}/rechazar",
    summary="CU11 - Taller rechaza una solicitud (queda disponible)",
    dependencies=[Depends(require_roles("TALLER"))],
)
async def rechazar_solicitud_endpoint(
    id_incidente: int,
    body: RechazoSolicitud,
    current_user: CurrentUser,
    db: DBDep,
):
    """El taller rechaza la solicitud. El incidente NO se elimina; se registra el rechazo
    en historial y la solicitud sigue disponible para otros talleres."""
    return await rechazar_solicitud(id_incidente, current_user.id_usuario, body.observacion, db)


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


@router.get(
    "/mis-metricas",
    summary="TALLER - Mis métricas de rendimiento",
    dependencies=[Depends(require_roles("TALLER"))],
)
async def mis_metricas(current_user: CurrentUser, db: DBDep):
    """El taller consulta sus propias estadísticas: solicitudes, servicios, ingresos y comisiones."""
    return await taller_service.obtener_metricas_taller(current_user.id_usuario, db)


@router.get(
    "/mis-pagos",
    summary="TALLER - Pagos y comisiones de los servicios atendidos",
    dependencies=[Depends(require_roles("TALLER"))],
)
async def mis_pagos_taller(current_user: CurrentUser, db: DBDep):
    """Lista los pagos relacionados con incidentes asignados a este taller, con su comisión."""
    return await taller_service.obtener_pagos_taller(current_user.id_usuario, db)


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
