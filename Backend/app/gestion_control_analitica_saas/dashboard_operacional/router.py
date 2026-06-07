from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.gestion_control_analitica_saas.dashboard_operacional import service
from app.gestion_control_analitica_saas.dashboard_operacional.schemas import DashboardOperacionalOut

router = APIRouter(
    prefix="/dashboard-operacional",
    tags=["dashboard-operacional"],
    dependencies=[Depends(require_roles("ADMINISTRADOR", "TALLER"))],
)


@router.get("", response_model=DashboardOperacionalOut)
async def get_dashboard(
    fecha_desde:   datetime | None = Query(None),
    fecha_hasta:   datetime | None = Query(None),
    id_taller:     int | None      = Query(None),
    clasificacion: str | None      = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await service.obtener_dashboard(
        id_tenant=current_user.id_tenant,
        db=db,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        id_taller=id_taller,
        clasificacion=clasificacion,
    )
