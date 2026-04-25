from fastapi import APIRouter, status, Depends
from app.core.dependencies import DBDep, CurrentUser, require_roles
from app.schemas.incidente import IncidenteOut, IncidenteCreate, IncidenteHistorialOut, IncidenteEstadoUpdate
from app.services import incidente_service
from app.services.asignacion_service import asignar_taller_optimo

router = APIRouter(
    prefix="/incidentes",
    tags=["Incidentes", "CU13"],
    dependencies=[Depends(require_roles("CLIENTE", "ADMINISTRADOR", "TALLER"))]
)

@router.patch(
    "/{id_incidente}/estado",
    response_model=IncidenteOut,
    status_code=status.HTTP_200_OK,
    summary="CU13 - Actualizar estado del servicio",
    description="Permite a un taller actualizar el estado de un servicio asignado. Y registrarlo al historial.",
    dependencies=[Depends(require_roles("TALLER", "ADMINISTRADOR"))]
)
async def actualizar_estado_servicio(id_incidente: int, estado_update: IncidenteEstadoUpdate, db: DBDep, current_user: CurrentUser):
    return await incidente_service.actualizar_estado_incidente(id_incidente, current_user.id_usuario, estado_update, db)

@router.get(
    "/{id_incidente}/historial",
    response_model=list[IncidenteHistorialOut],
    status_code=status.HTTP_200_OK,
    summary="CU13 - Consultar historial de estados del servicio",
    description="Permite al cliente o al taller consultar el histórico de estados actualizados.",
)
async def consultar_historial_servicio(id_incidente: int, db: DBDep, current_user: CurrentUser):
    es_admin = any(rol.nombre == "ADMINISTRADOR" for rol in current_user.roles) 
    es_taller = any(rol.nombre == "TALLER" for rol in current_user.roles)       
    return await incidente_service.consultar_historial_servicio(id_incidente, current_user.id_usuario, es_admin, es_taller, db)

@router.post(
    "",
    response_model=IncidenteOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un incidente inteligente",
    description="Permite al cliente registrar una emergencia vehicular que es procesada por clasificación IA basándose en texto, audio e imágenes.",
    dependencies=[Depends(require_roles("CLIENTE"))]
)
async def registrar_incidente(incidente: IncidenteCreate, db: DBDep, current_user: CurrentUser):
    return await incidente_service.registrar_incidente_inteligente(incidente, current_user.id_usuario, db)

@router.get(
    "",
    response_model=list[IncidenteOut],
    status_code=status.HTTP_200_OK,
    summary="Consultar historial de incidentes",
    description="Permite consultar el historial de incidentes registrados y su estado. Si es cliente, solo ve los suyos. Si es administrador, ve todos."        
)
async def consultar_incidentes(db: DBDep, current_user: CurrentUser):
    es_admin = any(rol.nombre == "ADMINISTRADOR" for rol in current_user.roles) 
    es_taller = any(rol.nombre == "TALLER" for rol in current_user.roles)       
    return await incidente_service.consultar_historial_incidentes(current_user.id_usuario, es_admin, es_taller, db)

@router.get(
    "/{id_incidente}",
    response_model=IncidenteOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar detalle de un incidente específico",
    description="Devuelve la información ampliada de un incidente."
)
async def obtener_detalle_incidente(id_incidente: int, db: DBDep, current_user: CurrentUser):
    es_admin = any(rol.nombre == "ADMINISTRADOR" for rol in current_user.roles)
    es_taller = any(rol.nombre == "TALLER" for rol in current_user.roles)
    return await incidente_service.obtener_detalle_incidente(id_incidente, current_user.id_usuario, es_admin, es_taller, db)

@router.post(
    "/{id_incidente}/asignar-taller",
    response_model=IncidenteOut,
    status_code=status.HTTP_200_OK,
    summary="CU12 - Asignar taller adecuado (Auto)",
    description="Simula el momento en el que el sistema analiza el incidente clasificado y evalúa los talleres disponibles para asignar automáticamente el óptimo. Notificándolo simuladamente.",
    dependencies=[Depends(require_roles("ADMINISTRADOR"))] # Asumimos que lo dispara un CRON, webhook o sistema ADMIN
)
async def procesar_asignacion_taller(id_incidente: int, db: DBDep, current_user: CurrentUser):
    return await asignar_taller_optimo(id_incidente, db)
from fastapi import APIRouter, status, Depends
from app.core.dependencies import DBDep, CurrentUser, require_roles
from app.schemas.incidente import IncidenteOut, IncidenteCreate, IncidenteHistorialOut, IncidenteEstadoUpdate
from app.services import incidente_service
from app.services.asignacion_service import asignar_taller_optimo

router = APIRouter(
    prefix="/incidentes",
    tags=["Incidentes", "CU13"],
    dependencies=[Depends(require_roles("CLIENTE", "ADMINISTRADOR", "TALLER"))]
)

@router.patch(
    "/{id_incidente}/estado",
    response_model=IncidenteOut,
    status_code=status.HTTP_200_OK,
    summary="CU13 - Actualizar estado del servicio",
    description="Permite a un taller actualizar el estado de un servicio asignado. Y registrarlo al historial.",
    dependencies=[Depends(require_roles("TALLER"))]
)
async def actualizar_estado_servicio(id_incidente: int, estado_update: IncidenteEstadoUpdate, db: DBDep, current_user: CurrentUser):
    return await incidente_service.actualizar_estado_incidente(id_incidente, current_user.id_usuario, estado_update, db)

@router.get(
    "/{id_incidente}/historial",
    response_model=list[IncidenteHistorialOut],
    status_code=status.HTTP_200_OK,
    summary="CU13 - Consultar historial de estados del servicio",
    description="Permite al cliente o al taller consultar el histórico de estados actualizados.",
)
async def consultar_historial_servicio(id_incidente: int, db: DBDep, current_user: CurrentUser):
    es_admin = any(rol.nombre == "ADMINISTRADOR" for rol in current_user.roles)
    es_taller = any(rol.nombre == "TALLER" for rol in current_user.roles)
    return await incidente_service.consultar_historial_servicio(id_incidente, current_user.id_usuario, es_admin, es_taller, db)

@router.post(
    "",
    response_model=IncidenteOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un incidente inteligente",
    description="Permite al cliente registrar una emergencia vehicular que es procesada por clasificación IA basándose en texto, audio e imágenes.",
    dependencies=[Depends(require_roles("CLIENTE"))]
)
async def registrar_incidente(incidente: IncidenteCreate, db: DBDep, current_user: CurrentUser):
    return await incidente_service.registrar_incidente_inteligente(incidente, current_user.id_usuario, db)

@router.get(
    "",
    response_model=list[IncidenteOut],
    status_code=status.HTTP_200_OK,
    summary="Consultar historial de incidentes",
    description="Permite consultar el historial de incidentes registrados y su estado. Si es cliente, solo ve los suyos. Si es administrador, ve todos."
)
async def consultar_incidentes(db: DBDep, current_user: CurrentUser):
    es_admin = any(rol.nombre == "ADMINISTRADOR" for rol in current_user.roles)
    es_taller = any(rol.nombre == "TALLER" for rol in current_user.roles)
    return await incidente_service.consultar_historial_incidentes(current_user.id_usuario, es_admin, es_taller, db)
    es_admin = any(rol.nombre == "ADMINISTRADOR" for rol in current_user.roles)
    return await incidente_service.obtener_detalle_incidente(id_incidente, current_user.id_usuario, es_admin, db)

@router.post(
    "/{id_incidente}/asignar-taller",
    response_model=IncidenteOut,
    status_code=status.HTTP_200_OK,
    summary="CU12 - Asignar taller adecuado (Auto)",
    description="Simula el momento en el que el sistema analiza el incidente clasificado y evalúa los talleres disponibles para asignar automáticamente el óptimo. Notificándolo simuladamente.",
    dependencies=[Depends(require_roles("ADMINISTRADOR"))] # Asumimos que lo dispara un CRON, webhook o sistema ADMIN
)
async def procesar_asignacion_taller(id_incidente: int, db: DBDep, current_user: CurrentUser):
    return await asignar_taller_optimo(id_incidente, db)
