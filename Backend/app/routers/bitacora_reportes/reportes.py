from fastapi import APIRouter, Depends
from typing import Optional

from app.core.dependencies import DBDep, CurrentUser, require_roles
from app.schemas.reporte import (
    ResumenGeneral, ReporteIncidentes, ReporteUsuarios,
    ReporteTalleres, ReportePagos,
)
from app.services import reporte_service

router = APIRouter(
    prefix="/reportes",
    tags=["Reportes", "CU17"],
    dependencies=[Depends(require_roles("ADMINISTRADOR"))],
)


@router.get("/resumen", response_model=ResumenGeneral)
async def resumen(db: DBDep, _: CurrentUser):
    return await reporte_service.resumen_general(db)


@router.get("/incidentes", response_model=ReporteIncidentes)
async def incidentes(
    db: DBDep,
    _: CurrentUser,
    desde:     Optional[str] = None,
    hasta:     Optional[str] = None,
    estado:    Optional[str] = None,
    id_taller: Optional[int] = None,
):
    return await reporte_service.reporte_incidentes(db, desde, hasta, estado, id_taller)


@router.get("/usuarios", response_model=ReporteUsuarios)
async def usuarios(
    db: DBDep,
    _: CurrentUser,
    desde: Optional[str] = None,
    hasta: Optional[str] = None,
    rol:   Optional[str] = None,
):
    return await reporte_service.reporte_usuarios(db, desde, hasta, rol)


@router.get("/talleres", response_model=ReporteTalleres)
async def talleres(db: DBDep, _: CurrentUser):
    return await reporte_service.reporte_talleres(db)


@router.get("/pagos", response_model=ReportePagos)
async def pagos(
    db: DBDep,
    _: CurrentUser,
    desde:  Optional[str] = None,
    hasta:  Optional[str] = None,
    estado: Optional[str] = None,
    metodo: Optional[str] = None,
):
    return await reporte_service.reporte_pagos(db, desde, hasta, estado, metodo)
