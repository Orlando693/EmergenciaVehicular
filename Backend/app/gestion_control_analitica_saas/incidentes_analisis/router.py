from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.gestion_control_analitica_saas.incidentes_analisis import service
from app.gestion_control_analitica_saas.incidentes_analisis.schemas import IncidentesAnalisisOut

router = APIRouter(
    prefix="/incidentes-analisis",
    tags=["incidentes-analisis"],
    dependencies=[Depends(require_roles("ADMINISTRADOR", "TALLER"))],
)


@router.get("", response_model=IncidentesAnalisisOut)
async def get_analisis(
    fecha_desde: datetime | None = Query(None),
    fecha_hasta: datetime | None = Query(None),
    tipo:        str | None      = Query(None),
    estado:      str | None      = Query(None),
    zona:        str | None      = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await service.obtener_analisis(
        id_tenant=current_user.id_tenant,
        db=db,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        tipo=tipo,
        estado=estado,
        zona=zona,
    )
