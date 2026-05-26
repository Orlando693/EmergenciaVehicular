from fastapi import APIRouter, status, Depends
from app.core.dependencies import DBDep, CurrentUser, require_roles
from app.schemas.vehiculo import VehiculoCreate, VehiculoUpdate, VehiculoOut
from app.services import vehiculo_service

router = APIRouter(
    prefix="/vehiculos", 
    tags=["Vehículos"],
    dependencies=[Depends(require_roles("CLIENTE"))]
)

@router.post(
    "",
    response_model=VehiculoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo vehículo",
    description="Permite a un cliente autenticado registrar un nuevo vehículo en el sistema"
)
async def registrar_vehiculo(vehiculo: VehiculoCreate, db: DBDep, current_user: CurrentUser):
    return await vehiculo_service.registrar_vehiculo(vehiculo, current_user.id_usuario, db)

@router.get(
    "",
    response_model=list[VehiculoOut],
    status_code=status.HTTP_200_OK,
    summary="Consultar vehículos",
    description="Obtiene todos los vehículos asociados al cliente autenticado"
)
async def consultar_vehiculos(db: DBDep, current_user: CurrentUser):
    return await vehiculo_service.consultar_vehiculos_cliente(current_user.id_usuario, db)

@router.get(
    "/{id_vehiculo}",
    response_model=VehiculoOut,
    status_code=status.HTTP_200_OK,
    summary="Obtener detalle de un vehículo",
    description="Obtiene los detalles de un vehículo específico que pertenece al cliente"
)
async def obtener_vehiculo(id_vehiculo: int, db: DBDep, current_user: CurrentUser):
    return await vehiculo_service.obtener_vehiculo(id_vehiculo, current_user.id_usuario, db)

@router.patch(
    "/{id_vehiculo}",
    response_model=VehiculoOut,
    status_code=status.HTTP_200_OK,
    summary="Actualizar un vehículo",
    description="Permite a un cliente autenticado actualizar la información de su vehículo"
)
async def actualizar_vehiculo(id_vehiculo: int, vehiculo_update: VehiculoUpdate, db: DBDep, current_user: CurrentUser):
    return await vehiculo_service.actualizar_vehiculo(id_vehiculo, vehiculo_update, current_user.id_usuario, db)
