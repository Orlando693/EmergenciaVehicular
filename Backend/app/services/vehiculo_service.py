from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.vehiculo import Vehiculo
from app.models.cliente import Cliente
from app.schemas.vehiculo import VehiculoCreate, VehiculoUpdate, VehiculoOut

async def get_cliente_by_usuario_id(id_usuario: int, db: AsyncSession) -> Cliente:
    result = await db.execute(select(Cliente).where(Cliente.id_usuario == id_usuario))
    cliente = result.scalar_one_or_none()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado asociado a este usuario"
        )
    return cliente

async def registrar_vehiculo(data: VehiculoCreate, id_usuario: int, db: AsyncSession) -> VehiculoOut:
    cliente = await get_cliente_by_usuario_id(id_usuario, db)
    
    # Verificar si la placa ya existe para evitar errores no controlados
    stmt = select(Vehiculo).where(Vehiculo.placa == data.placa)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un vehículo con esa placa ya se encuentra registrado"
        )

    nuevo_vehiculo = Vehiculo(
        id_cliente=cliente.id_cliente,
        placa=data.placa,
        marca=data.marca,
        modelo=data.modelo,
        anio=data.anio,
        color=data.color,
        tipo_vehiculo=data.tipo_vehiculo,
        vin=data.vin
    )
    db.add(nuevo_vehiculo)
    
    try:
        await db.commit()
        await db.refresh(nuevo_vehiculo)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Error de integridad, posible placa duplicada")

    return VehiculoOut.model_validate(nuevo_vehiculo)

async def consultar_vehiculos_cliente(id_usuario: int, db: AsyncSession) -> list[VehiculoOut]:
    cliente = await get_cliente_by_usuario_id(id_usuario, db)
    
    stmt = select(Vehiculo).where(Vehiculo.id_cliente == cliente.id_cliente)
    result = await db.execute(stmt)
    vehiculos = result.scalars().all()
    
    return [VehiculoOut.model_validate(v) for v in vehiculos]

async def actualizar_vehiculo(id_vehiculo: int, data: VehiculoUpdate, id_usuario: int, db: AsyncSession) -> VehiculoOut:
    cliente = await get_cliente_by_usuario_id(id_usuario, db)
    
    stmt = select(Vehiculo).where(Vehiculo.id_vehiculo == id_vehiculo, Vehiculo.id_cliente == cliente.id_cliente)
    result = await db.execute(stmt)
    vehiculo = result.scalar_one_or_none()
    
    if not vehiculo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehículo no encontrado o no pertenece a este cliente"
        )
    
    update_data = data.model_dump(exclude_unset=True)
    
    # If placa is being updated, verify it doesn't already exist for another vehicle
    if "placa" in update_data and update_data["placa"] != vehiculo.placa:
        placa_stmt = select(Vehiculo).where(Vehiculo.placa == update_data["placa"])
        placa_result = await db.execute(placa_stmt)
        if placa_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un vehículo con esa placa ya se encuentra registrado"
            )

    for field, value in update_data.items():
        setattr(vehiculo, field, value)
        
    try:
        await db.commit()
        await db.refresh(vehiculo)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Error validando los datos (posible registro duplicado)")

    return VehiculoOut.model_validate(vehiculo)

async def obtener_vehiculo(id_vehiculo: int, id_usuario: int, db: AsyncSession) -> VehiculoOut:
    cliente = await get_cliente_by_usuario_id(id_usuario, db)
    
    stmt = select(Vehiculo).where(Vehiculo.id_vehiculo == id_vehiculo, Vehiculo.id_cliente == cliente.id_cliente)
    result = await db.execute(stmt)
    vehiculo = result.scalar_one_or_none()
    
    if not vehiculo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehículo no encontrado o no pertenece a este cliente"
        )
        
    return VehiculoOut.model_validate(vehiculo)