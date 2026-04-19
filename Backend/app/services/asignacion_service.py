import math
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.taller import Taller
from app.models.incidente import Incidente
from app.schemas.incidente import IncidenteOut
from app.services.incidente_service import obtener_detalle_incidente

def calcular_distancia(lat1: float | None, lon1: float | None, lat2: float | None, lon2: float | None) -> float:
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return float('inf')
    
    R = 6371.0 # Radio de la Tierra en km
    lat1_rad = math.radians(float(lat1))
    lon1_rad = math.radians(float(lon1))
    lat2_rad = math.radians(float(lat2))
    lon2_rad = math.radians(float(lon2))

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

async def asignar_taller_optimo(id_incidente: int, db: AsyncSession) -> IncidenteOut:
    # 1. Obtener el incidente
    stmt = select(Incidente).where(
        Incidente.id_incidente == id_incidente,
        Incidente.id_taller.is_(None),
        Incidente.estado == "REPORTADO"
    )
    result = await db.execute(stmt)
    incidente = result.scalar_one_or_none()
    
    if not incidente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incidente no encontrado, o ya fue asignado/procesado."
        )

    # 2. Buscar talleres disponibles
    # Para el mock, asumiremos que un taller disponible tiene estado_registro = 'APROBADO' 
    # y consideraremos 'capacidad_maxima' o 'calificacion' simulada
    stmt_talleres = select(Taller).where(Taller.estado_registro == "APROBADO")
    res_talleres = await db.execute(stmt_talleres)
    talleres_aprobados = res_talleres.scalars().all()
    
    if not talleres_aprobados:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay talleres disponibles en este momento."
        )

    # 3. Seleccionar el mejor taller (Cálculo)
    taller_optimo = None
    menor_distancia = float('inf')
    
    for taller in talleres_aprobados:
        # Aquí evaluamos tipo de problema, capacidad y ubicación para la asignación ideal
        # Si es colisión y el taller no tiene equipo se podría saltar (lógica mock)
        
        # Filtro de cercanía
        dist = calcular_distancia(
            incidente.ubicacion_lat, incidente.ubicacion_lng,
            taller.latitud, taller.longitud
        )
        
        # Simulación de prioridad combinada: distancia + disponibilidad de capacidad (aún no se cuenta ocupación en crudo)
        if dist < menor_distancia:
            menor_distancia = dist
            taller_optimo = taller
            
    if not taller_optimo:
        # En caso de que nadie tenga lat/lng válido, seleccionamos uno por defecto
        taller_optimo = talleres_aprobados[0]

    # 4. Asignación y Notificación (MOCK)
    incidente.id_taller = taller_optimo.id_taller
    incidente.estado = "EN_PROCESO"
    
    db.add(incidente)
    await db.commit()
    await db.refresh(incidente)
    
    # 5. (Opcional mock) En un sistema real aquí se enviaría push notification o email al taller
    print(f"[Notificación] -> Taller '{taller_optimo.razon_social}': ¡Tienes un nuevo incidente de {incidente.clasificacion_ia} asignado!")

    # Retornar el detalle ya cruzado
    return await obtener_detalle_incidente(incidente.id_incidente, 0, es_admin=True, db=db)
