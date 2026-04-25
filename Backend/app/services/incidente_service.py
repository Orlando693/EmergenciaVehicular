from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.incidente import Incidente
from app.models.cliente import Cliente
from app.models.taller import Taller
from app.models.vehiculo import Vehiculo
from app.models.incidente import Incidente, IncidenteHistorial
from app.schemas.incidente import IncidenteOut, IncidenteCreate, IncidenteHistorialOut, IncidenteEstadoUpdate
import asyncio

async def procesar_con_ia_mock(descripcion: str, audio_url: str | None, imagen_url: str | None) -> dict:
    """ Simula el procesamiento con un motor IA """
    await asyncio.sleep(1) # Simula retraso
    # Logica simulada que un modelo analizó el caso
    clasificacion = "MECÁNICO"
    if "choque" in descripcion.lower() or "accidente" in descripcion.lower():
        clasificacion = "COLISIÓN"
    elif "neumatico" in descripcion.lower() or "llanta" in descripcion.lower():
        clasificacion = "NEUMÁTICOS"
        
    fuentes = ["texto"]
    if audio_url:
        fuentes.append("audio")
    if imagen_url:
        fuentes.append("imagen")
        
    resumen = f"Problema {clasificacion} reportado. Análisis basado en {', '.join(fuentes)}."
    
    return {
        "clasificacion": clasificacion,
        "resumen": resumen
    }

async def registrar_incidente_inteligente(data: IncidenteCreate, id_usuario: int, db: AsyncSession) -> IncidenteOut:
    cliente = await get_cliente_by_usuario_id(id_usuario, db)
    
    # 1. Validar vehículo
    vehiculo_stmt = select(Vehiculo).where(Vehiculo.id_vehiculo == data.id_vehiculo, Vehiculo.id_cliente == cliente.id_cliente)
    veh_result = await db.execute(vehiculo_stmt)
    vehiculo = veh_result.scalar_one_or_none()
    
    if not vehiculo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El vehículo no existe o no pertenece al cliente"
        )
        
    if not data.descripcion and not data.audio_url and not data.imagen_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe proveer al menos texto, audio o imagen para procesar el incidente"
        )

    # 2. Procesamiento IA (Llamada al agente/modelo)
    ia_result = await procesar_con_ia_mock(data.descripcion, data.audio_url, data.imagen_url)
    
    # 3. Guardar Incidente
    nuevo_incidente = Incidente(
        id_cliente=cliente.id_cliente,
        id_vehiculo=vehiculo.id_vehiculo,
        descripcion=data.descripcion,
        audio_url=data.audio_url,
        imagen_url=data.imagen_url,
        ubicacion_lat=data.ubicacion_lat,
        ubicacion_lng=data.ubicacion_lng,
        direccion=data.direccion,
        estado="REPORTADO",
        clasificacion_ia=ia_result["clasificacion"],
        resumen_ia=ia_result["resumen"]
    )
    
    db.add(nuevo_incidente)
    await db.commit()
    await db.refresh(nuevo_incidente)
    
    # Pre-cargar relaciones para responder
    return await obtener_detalle_incidente(nuevo_incidente.id_incidente, id_usuario, es_admin=False, db=db)

async def get_cliente_by_usuario_id(id_usuario: int, db: AsyncSession) -> Cliente:
    result = await db.execute(select(Cliente).where(Cliente.id_usuario == id_usuario))
    cliente = result.scalar_one_or_none()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado asociado a este usuario"
        )
    return cliente

async def consultar_historial_incidentes(id_usuario: int, es_admin: bool, es_taller: bool, db: AsyncSession) -> list[IncidenteOut]:
    stmt = select(Incidente).options(
        selectinload(Incidente.taller),
        selectinload(Incidente.vehiculo)
    ).order_by(Incidente.created_at.desc())

    if not es_admin:
        if es_taller:
            stmt_taller = select(Taller).where(Taller.id_usuario == id_usuario)
            res_taller = await db.execute(stmt_taller)
            taller = res_taller.scalar_one_or_none()
            id_taller = taller.id_taller if taller else -1
            stmt = stmt.where(Incidente.id_taller == id_taller)
        else:
            cliente = await get_cliente_by_usuario_id(id_usuario, db)
            stmt = stmt.where(Incidente.id_cliente == cliente.id_cliente)

    result = await db.execute(stmt)
    incidentes = result.scalars().all()
    
    response = []
    for inc in incidentes:
        inc_data = IncidenteOut.model_validate(inc)
        if inc.taller:
            inc_data.taller_nombre = inc.taller.razon_social
        if inc.vehiculo:
            inc_data.vehiculo_placa = inc.vehiculo.placa
            inc_data.vehiculo_marca = inc.vehiculo.marca
            inc_data.vehiculo_modelo = inc.vehiculo.modelo
        response.append(inc_data)

    return response

async def consultar_solicitudes_disponibles(db: AsyncSession) -> list[IncidenteOut]:
    """Obtiene todos los incidentes que están en estado REPORTADO y no tienen taller asignado."""
    stmt = select(Incidente).options(
        selectinload(Incidente.vehiculo)
    ).where(
        Incidente.estado == "REPORTADO",
        Incidente.id_taller.is_(None)
    ).order_by(Incidente.created_at.desc())

    result = await db.execute(stmt)
    incidentes = result.scalars().all()

    response = []
    for inc in incidentes:
        inc_data = IncidenteOut.model_validate(inc)
        if inc.vehiculo:
            inc_data.vehiculo_placa = inc.vehiculo.placa
            inc_data.vehiculo_marca = inc.vehiculo.marca
            inc_data.vehiculo_modelo = inc.vehiculo.modelo
        response.append(inc_data)

    return response

async def actualizar_estado_incidente(id_incidente: int, id_usuario: int, data: IncidenteEstadoUpdate, db: AsyncSession) -> IncidenteOut:
    stmt_taller = select(Taller).where(Taller.id_usuario == id_usuario)
    res_taller = await db.execute(stmt_taller)
    taller = res_taller.scalar_one_or_none()

    if not taller:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado o no es un taller válido")

    stmt = select(Incidente).where(
        Incidente.id_incidente == id_incidente,
        Incidente.id_taller == taller.id_taller
    )
    result = await db.execute(stmt)
    incidente = result.scalar_one_or_none()

    if not incidente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Servicio no encontrado o no asignado a este taller"
        )
    
    estado_viejo = incidente.estado
    if estado_viejo == data.estado:
        raise HTTPException(status_code=400, detail="El incidente ya se encuentra en este estado")
        
    incidente.estado = data.estado
    
    historial = IncidenteHistorial(
        id_incidente=incidente.id_incidente,
        estado_anterior=estado_viejo,
        estado_nuevo=data.estado,
        observacion=data.observacion
    )
    
    db.add(historial)
    db.add(incidente)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al actualizar el estado del servicio")
        
    return await obtener_detalle_incidente(id_incidente, 0, es_admin=True, db=db)

async def consultar_historial_servicio(id_incidente: int, id_usuario: int, es_admin: bool, es_taller: bool, db: AsyncSession) -> list[IncidenteHistorialOut]:
    stmt = select(Incidente).where(Incidente.id_incidente == id_incidente)
    if not es_admin:
        if es_taller:
            stmt_taller = select(Taller).where(Taller.id_usuario == id_usuario)
            taller = (await db.execute(stmt_taller)).scalar_one_or_none()
            stmt = stmt.where(Incidente.id_taller == (taller.id_taller if taller else -1))
        else:
            cliente = await get_cliente_by_usuario_id(id_usuario, db)
            stmt = stmt.where(Incidente.id_cliente == cliente.id_cliente)
            
    res = await db.execute(stmt)
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incidente no accesible")

    historial_stmt = select(IncidenteHistorial).where(IncidenteHistorial.id_incidente == id_incidente).order_by(IncidenteHistorial.created_at.desc())
    h_res = await db.execute(historial_stmt)
    return [IncidenteHistorialOut.model_validate(h) for h in h_res.scalars().all()]

async def obtener_detalle_solicitud(id_incidente: int, db: AsyncSession) -> IncidenteOut:
    """Obtiene el detalle de un incidente disponible (estado REPORTADO sin taller asignado)."""
    stmt = select(Incidente).options(
        selectinload(Incidente.vehiculo)
    ).where(
        Incidente.id_incidente == id_incidente,
        Incidente.estado == "REPORTADO",
        Incidente.id_taller.is_(None)
    )

    result = await db.execute(stmt)
    incidente = result.scalar_one_or_none()

    if not incidente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitud no encontrada o ya no está disponible"
        )

    inc_data = IncidenteOut.model_validate(incidente)
    if incidente.vehiculo:
        inc_data.vehiculo_placa = incidente.vehiculo.placa
        inc_data.vehiculo_marca = incidente.vehiculo.marca
        inc_data.vehiculo_modelo = incidente.vehiculo.modelo

    return inc_data

async def obtener_detalle_incidente(id_incidente: int, id_usuario: int, es_admin: bool, es_taller: bool, db: AsyncSession) -> IncidenteOut:
    """Obtiene el detalle de un incidente validando roles asignados."""
    stmt = select(Incidente).options(
        selectinload(Incidente.vehiculo),
        selectinload(Incidente.taller)
    ).where(Incidente.id_incidente == id_incidente)

    result = await db.execute(stmt)
    incidente = result.scalar_one_or_none()

    if not incidente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incidente no encontrado"
        )

    # Validar permisos
    if not es_admin:
        if es_taller:
            taller_stmt = select(Taller).where(Taller.id_usuario == id_usuario)
            taller_res = await db.execute(taller_stmt)
            taller = taller_res.scalar_one_or_none()
            if not taller or incidente.id_taller != taller.id_taller:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado para ver este servicio.")
        else:
            cliente_stmt = select(Cliente).where(Cliente.id_usuario == id_usuario)
            cliente_res = await db.execute(cliente_stmt)
            cliente = cliente_res.scalar_one_or_none()
            if not cliente or incidente.id_cliente != cliente.id_cliente:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado para ver este incidente.")

    inc_data = IncidenteOut.model_validate(incidente)
    if incidente.vehiculo:
        inc_data.vehiculo_placa = incidente.vehiculo.placa
        inc_data.vehiculo_marca = incidente.vehiculo.marca
        inc_data.vehiculo_modelo = incidente.vehiculo.modelo
    if incidente.taller:
        inc_data.taller_nombre = incidente.taller.razon_social

    return inc_data
    return inc_data

