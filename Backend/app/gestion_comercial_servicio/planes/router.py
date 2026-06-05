from fastapi import APIRouter, Depends

from app.core.dependencies import CurrentUser, DBDep, require_roles
from app.gestion_comercial_servicio.planes import service as planes_service
from app.gestion_comercial_servicio.planes.schemas import PlanOut, SuscripcionOut, SuscribirRequest

router = APIRouter(prefix="/planes", tags=["Planes", "CU28"])


@router.get("", response_model=list[PlanOut], summary="CU28 - Listar planes disponibles (público)")
async def listar_planes(db: DBDep):
    """Devuelve todos los planes activos. No requiere autenticación."""
    return await planes_service.listar_planes(db)


@router.get(
    "/mi-suscripcion",
    response_model=SuscripcionOut | None,
    summary="CU28 - Ver suscripción activa del tenant",
    dependencies=[Depends(require_roles("TALLER"))],
)
async def mi_suscripcion(db: DBDep, current_user: CurrentUser):
    return await planes_service.obtener_suscripcion_activa(current_user.id_tenant, db)


@router.post(
    "/suscribir",
    response_model=SuscripcionOut,
    status_code=201,
    summary="CU28 - Suscribirse a un plan",
    dependencies=[Depends(require_roles("TALLER"))],
)
async def suscribir(body: SuscribirRequest, db: DBDep, current_user: CurrentUser):
    return await planes_service.suscribir(current_user.id_tenant, body.id_plan, db)


@router.get(
    "/historial",
    response_model=list[SuscripcionOut],
    summary="CU28 - Historial de suscripciones del tenant",
    dependencies=[Depends(require_roles("TALLER"))],
)
async def historial(db: DBDep, current_user: CurrentUser):
    return await planes_service.historial_suscripciones(current_user.id_tenant, db)
