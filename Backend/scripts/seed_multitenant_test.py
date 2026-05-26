import asyncio
import sys
from decimal import Decimal
from pathlib import Path

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy import func, select

from app.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.bitacora import Bitacora
from app.models.cliente import Cliente
from app.models.enums import EstadoTallerEnum
from app.models.incidente import Incidente, IncidenteHistorial
from app.models.notificacion import Notificacion
from app.models.pago import Pago
from app.models.taller import Taller
from app.models.tenant import Tenant
from app.models.usuario import Rol, Usuario, UsuarioRol
from app.models.vehiculo import Vehiculo


PASSWORD = "Test1234"


async def get_or_create_tenant(db, nombre: str, slug: str) -> Tenant:
    result = await db.execute(select(Tenant).where(Tenant.slug == slug))
    tenant = result.scalar_one_or_none()
    if tenant:
        tenant.nombre = nombre
        tenant.estado = "ACTIVO"
        return tenant

    tenant = Tenant(nombre=nombre, slug=slug, estado="ACTIVO")
    db.add(tenant)
    await db.flush()
    return tenant


async def get_or_create_role(db, nombre: str) -> Rol:
    result = await db.execute(select(Rol).where(Rol.nombre == nombre))
    rol = result.scalar_one_or_none()
    if rol:
        return rol

    rol = Rol(nombre=nombre, descripcion=f"Rol {nombre} para pruebas multi-tenant")
    db.add(rol)
    await db.flush()
    return rol


async def assign_role(db, usuario: Usuario, rol: Rol) -> None:
    result = await db.execute(
        select(UsuarioRol).where(
            UsuarioRol.id_usuario == usuario.id_usuario,
            UsuarioRol.id_rol == rol.id_rol,
        )
    )
    if not result.scalar_one_or_none():
        db.add(UsuarioRol(id_usuario=usuario.id_usuario, id_rol=rol.id_rol))


async def get_or_create_user(db, tenant: Tenant, email: str, nombres: str, apellidos: str, rol: Rol) -> Usuario:
    result = await db.execute(select(Usuario).where(func.lower(Usuario.email) == email.lower()))
    usuario = result.scalar_one_or_none()
    if usuario:
        usuario.id_tenant = tenant.id_tenant
        usuario.nombres = nombres
        usuario.apellidos = apellidos
    else:
        usuario = Usuario(
            id_tenant=tenant.id_tenant,
            nombres=nombres,
            apellidos=apellidos,
            email=email,
            telefono="70000000",
            password_hash=hash_password(PASSWORD),
        )
        db.add(usuario)
        await db.flush()

    await assign_role(db, usuario, rol)
    return usuario


async def get_or_create_cliente(db, tenant: Tenant, usuario: Usuario) -> Cliente:
    result = await db.execute(
        select(Cliente).where(Cliente.id_usuario == usuario.id_usuario, Cliente.id_tenant == tenant.id_tenant)
    )
    cliente = result.scalar_one_or_none()
    if cliente:
        return cliente

    cliente = Cliente(
        id_tenant=tenant.id_tenant,
        id_usuario=usuario.id_usuario,
        ci=f"CI-{tenant.slug}",
        direccion=f"Direccion prueba {tenant.nombre}",
        referencia="Dato sintetico de prueba",
    )
    db.add(cliente)
    await db.flush()
    return cliente


async def get_or_create_taller(db, tenant: Tenant, usuario: Usuario, suffix: str) -> Taller:
    result = await db.execute(
        select(Taller).where(Taller.id_usuario == usuario.id_usuario, Taller.id_tenant == tenant.id_tenant)
    )
    taller = result.scalar_one_or_none()
    if taller:
        return taller

    taller = Taller(
        id_tenant=tenant.id_tenant,
        id_usuario=usuario.id_usuario,
        razon_social=f"Taller {tenant.nombre}",
        nombre_comercial=f"Taller {suffix}",
        nit=f"NIT-MT-{suffix}",
        telefono_atencion="70000001",
        email_atencion=usuario.email,
        direccion=f"Zona prueba {suffix}",
        referencia="Seed multi-tenant",
        latitud=Decimal("-16.5000000"),
        longitud=Decimal("-68.1500000"),
        capacidad_maxima=3,
        acepta_remolque=True,
        estado_registro=EstadoTallerEnum.APROBADO,
    )
    db.add(taller)
    await db.flush()
    return taller


async def get_or_create_vehiculo(db, tenant: Tenant, cliente: Cliente, placa: str) -> Vehiculo:
    result = await db.execute(select(Vehiculo).where(Vehiculo.placa == placa, Vehiculo.id_tenant == tenant.id_tenant))
    vehiculo = result.scalar_one_or_none()
    if vehiculo:
        return vehiculo

    vehiculo = Vehiculo(
        id_tenant=tenant.id_tenant,
        id_cliente=cliente.id_cliente,
        placa=placa,
        marca="Toyota",
        modelo="Corolla",
        anio=2020,
        color="Blanco",
        tipo_vehiculo="Automovil",
        vin=f"VIN-{placa}",
    )
    db.add(vehiculo)
    await db.flush()
    return vehiculo


async def get_or_create_incidente(db, tenant: Tenant, cliente: Cliente, vehiculo: Vehiculo, taller: Taller, suffix: str) -> Incidente:
    result = await db.execute(
        select(Incidente).where(
            Incidente.id_tenant == tenant.id_tenant,
            Incidente.descripcion == f"Incidente multi-tenant {suffix}",
        )
    )
    incidente = result.scalar_one_or_none()
    if incidente:
        return incidente

    incidente = Incidente(
        id_tenant=tenant.id_tenant,
        id_cliente=cliente.id_cliente,
        id_vehiculo=vehiculo.id_vehiculo,
        id_taller=taller.id_taller,
        descripcion=f"Incidente multi-tenant {suffix}",
        resumen_ia="Seed de prueba de aislamiento",
        clasificacion_ia="MECANICO",
        ubicacion_lat=-16.5,
        ubicacion_lng=-68.15,
        direccion=f"Direccion incidente {suffix}",
        estado="RESUELTO",
    )
    db.add(incidente)
    await db.flush()

    db.add(
        IncidenteHistorial(
            id_tenant=tenant.id_tenant,
            id_incidente=incidente.id_incidente,
            estado_anterior=None,
            estado_nuevo="RESUELTO",
            observacion="Historial seed multi-tenant",
        )
    )
    return incidente


async def get_or_create_pago(db, tenant: Tenant, cliente: Cliente, incidente: Incidente) -> Pago:
    result = await db.execute(
        select(Pago).where(Pago.id_tenant == tenant.id_tenant, Pago.id_incidente == incidente.id_incidente)
    )
    pago = result.scalar_one_or_none()
    if pago:
        return pago

    pago = Pago(
        id_tenant=tenant.id_tenant,
        id_incidente=incidente.id_incidente,
        id_cliente=cliente.id_cliente,
        monto_total=Decimal("100.00"),
        monto_taller=Decimal("90.00"),
        comision_plataforma=Decimal("10.00"),
        metodo_pago="EFECTIVO",
        estado="COMPLETADO",
        referencia=f"SEED-{tenant.slug}",
    )
    db.add(pago)
    await db.flush()
    return pago


async def create_audit_rows(db, tenant: Tenant, usuario: Usuario, incidente: Incidente) -> None:
    notif_exists = await db.execute(
        select(Notificacion).where(
            Notificacion.id_tenant == tenant.id_tenant,
            Notificacion.id_usuario == usuario.id_usuario,
            Notificacion.tipo == "SEED_MULTITENANT",
        )
    )
    if not notif_exists.scalar_one_or_none():
        db.add(
            Notificacion(
                id_tenant=tenant.id_tenant,
                id_usuario=usuario.id_usuario,
                id_incidente=incidente.id_incidente,
                titulo="Seed multi-tenant",
                mensaje=f"Notificacion de prueba para {tenant.nombre}",
                tipo="SEED_MULTITENANT",
            )
        )

    log_exists = await db.execute(
        select(Bitacora).where(
            Bitacora.id_tenant == tenant.id_tenant,
            Bitacora.modulo == "Seed multi-tenant",
            Bitacora.id_usuario == usuario.id_usuario,
        )
    )
    if not log_exists.scalar_one_or_none():
        db.add(
            Bitacora(
                id_tenant=tenant.id_tenant,
                modulo="Seed multi-tenant",
                accion=f"Datos sinteticos creados para {tenant.slug}",
                rol="ADMINISTRADOR",
                usuario_email=usuario.email,
                id_usuario=usuario.id_usuario,
            )
        )


async def seed_tenant(db, nombre: str, slug: str, suffix: str) -> dict:
    rol_admin = await get_or_create_role(db, "ADMINISTRADOR")
    rol_taller = await get_or_create_role(db, "TALLER")
    rol_cliente = await get_or_create_role(db, "CLIENTE")

    tenant = await get_or_create_tenant(db, nombre, slug)
    admin = await get_or_create_user(db, tenant, f"admin.{suffix.lower()}@test.com", f"Admin {suffix}", "Test", rol_admin)
    taller_user = await get_or_create_user(db, tenant, f"taller.{suffix.lower()}@test.com", f"Taller {suffix}", "Test", rol_taller)
    cliente_user = await get_or_create_user(db, tenant, f"cliente.{suffix.lower()}@test.com", f"Cliente {suffix}", "Test", rol_cliente)

    cliente = await get_or_create_cliente(db, tenant, cliente_user)
    taller = await get_or_create_taller(db, tenant, taller_user, suffix)
    vehiculo = await get_or_create_vehiculo(db, tenant, cliente, f"MT-{suffix}-001")
    incidente = await get_or_create_incidente(db, tenant, cliente, vehiculo, taller, suffix)
    pago = await get_or_create_pago(db, tenant, cliente, incidente)
    await create_audit_rows(db, tenant, admin, incidente)

    return {
        "tenant": tenant,
        "admin": admin,
        "taller_user": taller_user,
        "cliente_user": cliente_user,
        "taller": taller,
        "cliente": cliente,
        "vehiculo": vehiculo,
        "incidente": incidente,
        "pago": pago,
    }


async def main() -> None:
    async with AsyncSessionLocal() as db:
        data_a = await seed_tenant(db, "Auxilio Norte", "auxilio-norte", "A")
        data_b = await seed_tenant(db, "Mecanicos Express", "mecanicos-express", "B")
        await db.commit()

        for label, data in (("Tenant A", data_a), ("Tenant B", data_b)):
            print(f"{label}: {data['tenant'].nombre} ({data['tenant'].slug})")
            print(f"  id_tenant: {data['tenant'].id_tenant}")
            print(f"  admin: {data['admin'].email} / {PASSWORD}")
            print(f"  taller: {data['taller_user'].email} / {PASSWORD}")
            print(f"  cliente: {data['cliente_user'].email} / {PASSWORD}")
            print(f"  id_taller: {data['taller'].id_taller}")
            print(f"  id_vehiculo: {data['vehiculo'].id_vehiculo}")
            print(f"  id_incidente: {data['incidente'].id_incidente}")
            print(f"  id_pago: {data['pago'].id_pago}")


if __name__ == "__main__":
    asyncio.run(main())
