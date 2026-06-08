import os
import time
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.config import settings
from app.core.dependencies import DBDep, CurrentUser, require_roles
from app.bitacora_reportes.bitacora import service as bitacora_service
from app.bitacora_reportes.bitacora.schemas import BitacoraCreate
from app.bitacora_reportes.reportes.schemas import (
    ResumenGeneral, ReporteIncidentes, ReporteUsuarios,
    ReporteTalleres, ReportePagos, ReporteAudioOut,
)
from app.bitacora_reportes.reportes import service as reporte_service

router = APIRouter(
    prefix="/reportes",
    tags=["Reportes", "CU17"],
    dependencies=[Depends(require_roles("ADMINISTRADOR"))],
)


@router.get("/resumen", response_model=ResumenGeneral)
async def resumen(db: DBDep, current_user: CurrentUser):
    return await reporte_service.resumen_general(db, current_user.id_tenant)


@router.get("/incidentes", response_model=ReporteIncidentes)
async def incidentes(
    db: DBDep,
    current_user: CurrentUser,
    desde:     Optional[str] = None,
    hasta:     Optional[str] = None,
    estado:    Optional[str] = None,
    id_taller: Optional[int] = None,
):
    return await reporte_service.reporte_incidentes(db, current_user.id_tenant, desde, hasta, estado, id_taller)


@router.get("/usuarios", response_model=ReporteUsuarios)
async def usuarios(
    db: DBDep,
    current_user: CurrentUser,
    desde: Optional[str] = None,
    hasta: Optional[str] = None,
    rol:   Optional[str] = None,
):
    return await reporte_service.reporte_usuarios(db, current_user.id_tenant, desde, hasta, rol)


@router.get("/talleres", response_model=ReporteTalleres)
async def talleres(db: DBDep, current_user: CurrentUser):
    return await reporte_service.reporte_talleres(db, current_user.id_tenant)


@router.get("/pagos", response_model=ReportePagos)
async def pagos(
    db: DBDep,
    current_user: CurrentUser,
    desde:  Optional[str] = None,
    hasta:  Optional[str] = None,
    estado: Optional[str] = None,
    metodo: Optional[str] = None,
):
    return await reporte_service.reporte_pagos(db, current_user.id_tenant, desde, hasta, estado, metodo)


@router.post(
    "/audio",
    response_model=ReporteAudioOut,
    status_code=status.HTTP_201_CREATED,
    summary="ADMIN - Enviar reporte por audio",
)
async def subir_reporte_audio(
    db: DBDep,
    current_user: CurrentUser,
    file: Annotated[UploadFile, File(description="Audio del reporte administrativo")],
):
    content_type = file.content_type or "application/octet-stream"
    if not content_type.startswith("audio/") and content_type != "application/octet-stream":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo debe ser un audio.",
        )

    data = await file.read()
    max_size = 15 * 1024 * 1024
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El audio esta vacio.")
    if len(data) > max_size:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="El audio supera 15 MB.")

    tenant_dir = os.path.join(settings.UPLOAD_DIR, str(current_user.id_tenant), "reportes", "audio")
    os.makedirs(tenant_dir, exist_ok=True)

    extension = os.path.splitext(file.filename or "")[1] or ".m4a"
    safe_extension = "".join(ch for ch in extension.lower() if ch.isalnum() or ch == ".")[:10] or ".m4a"
    filename = f"reporte_{int(time.time())}_{current_user.id_usuario}{safe_extension}"
    file_location = os.path.join(tenant_dir, filename)

    with open(file_location, "wb") as f:
        f.write(data)

    url = f"{settings.UPLOAD_URL_PREFIX}/{current_user.id_tenant}/reportes/audio/{filename}"
    await bitacora_service.create_log(
        db,
        BitacoraCreate(
            modulo="Reportes",
            accion=f"Envio reporte por audio: {url}",
            rol="ADMINISTRADOR",
            usuario_email=current_user.email,
            id_usuario=current_user.id_usuario,
        ),
        current_user.id_tenant,
    )

    return ReporteAudioOut(
        url=url,
        filename=filename,
        content_type=content_type,
        size_bytes=len(data),
        mensaje="Audio de reporte recibido correctamente.",
    )
