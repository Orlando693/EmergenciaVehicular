import os
import time
from typing import Annotated
from fastapi import APIRouter, status, Depends, UploadFile, File
from app.config import settings
from app.core.dependencies import DBDep, CurrentUser, require_roles
from app.schemas.incidente import IncidenteOut, IncidenteCreate, IncidenteHistorialOut, IncidenteEstadoUpdate
from app.services import incidente_service
from app.services.asignacion_service import asignar_taller_optimo

router = APIRouter(
    prefix="/incidentes",
    tags=["Incidentes", "CU10", "CU13"],
    dependencies=[Depends(require_roles("CLIENTE", "ADMINISTRADOR", "TALLER"))]
)

@router.post(
    "/upload",
    status_code=status.HTTP_200_OK,
    summary="Subir un archivo (Foto/Audio)",
    dependencies=[Depends(require_roles("CLIENTE", "ADMINISTRADOR"))]
)
async def upload_file(
    file: Annotated[UploadFile, File(description="Imagen o audio de evidencia")],
    current_user: CurrentUser
):
    """
    Sube un archivo de evidencia (imagen o audio) al servidor para ser procesado por la IA.
    Retorna la URL relativa para adjuntar al payload de IncidenteCreate.

    El directorio físico de almacenamiento se controla con la variable de entorno
    UPLOAD_DIR (por defecto "public/uploads"). En Railway, configurar
    UPLOAD_DIR=/data/uploads y montar un Volume en /data para persistencia.
    """
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    extension = os.path.splitext(file.filename or "")[1]
    filename = f"{int(time.time())}_{current_user.id_usuario}{extension}"
    file_location = os.path.join(settings.UPLOAD_DIR, filename)

    with open(file_location, "wb") as f:
        f.write(await file.read())

    return {"url": f"{settings.UPLOAD_URL_PREFIX}/{filename}"}

@router.patch(
    "/{id_incidente}/estado",
    response_model=IncidenteOut,
    status_code=status.HTTP_200_OK,
    summary="CU13 - Actualizar estado del servicio",
    dependencies=[Depends(require_roles("TALLER", "ADMINISTRADOR"))]
)
async def actualizar_estado_servicio(id_incidente: int, estado_update: IncidenteEstadoUpdate, db: DBDep, current_user: CurrentUser):
    return await incidente_service.actualizar_estado_incidente(id_incidente, current_user.id_usuario, estado_update, db)

@router.get(
    "/{id_incidente}/historial",
    response_model=list[IncidenteHistorialOut],
    status_code=status.HTTP_200_OK,
    summary="CU13 - Consultar historial de estados del servicio",
)
async def consultar_historial_servicio(id_incidente: int, db: DBDep, current_user: CurrentUser):
    es_admin = any(rol.nombre == "ADMINISTRADOR" for rol in current_user.roles) 
    es_taller = any(rol.nombre == "TALLER" for rol in current_user.roles)       
    return await incidente_service.consultar_historial_servicio(id_incidente, current_user.id_usuario, es_admin, es_taller, db)

@router.get(
    "/mis-metricas",
    summary="CLIENTE - Resumen de mis incidentes y pagos",
    dependencies=[Depends(require_roles("CLIENTE"))],
)
async def mis_metricas_cliente(db: DBDep, current_user: CurrentUser):
    """El cliente consulta el resumen de sus incidentes y pagos."""
    return await incidente_service.obtener_metricas_cliente(current_user.id_usuario, db)


@router.post(
    "",
    response_model=IncidenteOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un incidente inteligente (CU10)",
    dependencies=[Depends(require_roles("CLIENTE"))]
)
async def registrar_incidente(incidente: IncidenteCreate, db: DBDep, current_user: CurrentUser):
    return await incidente_service.registrar_incidente_inteligente(incidente, current_user.id_usuario, db)

@router.get(
    "",
    response_model=list[IncidenteOut],
    status_code=status.HTTP_200_OK,
    summary="Consultar historial de incidentes"
)
async def consultar_incidentes(db: DBDep, current_user: CurrentUser):
    es_admin = any(rol.nombre == "ADMINISTRADOR" for rol in current_user.roles) 
    es_taller = any(rol.nombre == "TALLER" for rol in current_user.roles)       
    return await incidente_service.consultar_historial_incidentes(current_user.id_usuario, es_admin, es_taller, db)

@router.get(
    "/{id_incidente}",
    response_model=IncidenteOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar detalle de un incidente especÃfico"
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
    dependencies=[Depends(require_roles("ADMINISTRADOR"))]
)
async def procesar_asignacion_taller(id_incidente: int, db: DBDep, current_user: CurrentUser):
    return await asignar_taller_optimo(id_incidente, db)
