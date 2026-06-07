"""
Script de seed para desarrollo local.
Crea el tenant principal y los usuarios de prueba con sus roles.

Uso:
    cd Backend
    ../.venv/Scripts/python.exe scripts/seed_local.py
"""

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
from app.core.enums import EstadoTallerEnum, EstadoUsuarioEnum

# Importar hub de modelos PRIMERO para que SQLAlchemy resuelva todas las relaciones
import app.models  # noqa: F401

from app.administracion.tenants.model import Tenant
from app.administracion.usuarios.model import Usuario, Rol, UsuarioRol, Cliente
from app.operaciones.talleres.model import Taller
from app.gestion_comercial_servicio.planes.model import Plan, TenantSuscripcion
from app.plataform_superAdmin.model import SuperAdmin

TENANT_NOMBRE = "EmergenciaVehicular"
TENANT_SLUG   = "emergencia-vehicular"

USUARIOS = [
    {"email": "admin@emergencia.com",   "password": "Admin1234",   "nombres": "Admin",   "apellidos": "Sistema",    "rol": "ADMINISTRADOR"},
    {"email": "taller@emergencia.com",  "password": "Taller1234",  "nombres": "Taller",  "apellidos": "Principal",  "rol": "TALLER"},
    {"email": "cliente@emergencia.com", "password": "Cliente1234", "nombres": "Cliente", "apellidos": "Prueba",     "rol": "CLIENTE"},
]


async def get_or_create_tenant(db) -> Tenant:
    res = await db.execute(select(Tenant).where(Tenant.slug == TENANT_SLUG))
    tenant = res.scalar_one_or_none()
    if tenant:
        tenant.nombre = TENANT_NOMBRE
        tenant.estado = "ACTIVO"
        print(f"  [OK] Tenant existente actualizado: {TENANT_NOMBRE} (id={tenant.id_tenant})")
        return tenant

    tenant = Tenant(nombre=TENANT_NOMBRE, slug=TENANT_SLUG, estado="ACTIVO")
    db.add(tenant)
    await db.flush()
    print(f"  [+] Tenant creado: {TENANT_NOMBRE} (id={tenant.id_tenant})")
    return tenant


async def get_or_create_rol(db, nombre: str) -> Rol:
    res = await db.execute(select(Rol).where(Rol.nombre == nombre))
    rol = res.scalar_one_or_none()
    if not rol:
        rol = Rol(nombre=nombre, descripcion=f"Rol {nombre}")
        db.add(rol)
        await db.flush()
    return rol


async def assign_rol(db, usuario: Usuario, rol: Rol) -> None:
    res = await db.execute(
        select(UsuarioRol).where(
            UsuarioRol.id_usuario == usuario.id_usuario,
            UsuarioRol.id_rol == rol.id_rol,
        )
    )
    if not res.scalar_one_or_none():
        db.add(UsuarioRol(id_usuario=usuario.id_usuario, id_rol=rol.id_rol))


async def seed_usuario(db, tenant: Tenant, data: dict) -> Usuario:
    res = await db.execute(select(Usuario).where(func.lower(Usuario.email) == data["email"].lower()))
    usuario = res.scalar_one_or_none()

    if usuario:
        usuario.id_tenant = tenant.id_tenant
        usuario.nombres   = data["nombres"]
        usuario.apellidos = data["apellidos"]
        usuario.password_hash = hash_password(data["password"])
        usuario.estado    = EstadoUsuarioEnum.ACTIVO
        action = "actualizado"
    else:
        usuario = Usuario(
            id_tenant=tenant.id_tenant,
            nombres=data["nombres"],
            apellidos=data["apellidos"],
            email=data["email"],
            telefono="70000000",
            password_hash=hash_password(data["password"]),
            estado=EstadoUsuarioEnum.ACTIVO,
        )
        db.add(usuario)
        action = "creado"

    await db.flush()
    rol = await get_or_create_rol(db, data["rol"])
    await assign_rol(db, usuario, rol)
    print(f"  [{'+' if action == 'creado' else 'OK'}] Usuario {action}: {data['email']} / {data['password']}  [{data['rol']}]")
    return usuario


async def seed_taller(db, tenant: Tenant, usuario: Usuario) -> None:
    res = await db.execute(
        select(Taller).where(Taller.id_usuario == usuario.id_usuario, Taller.id_tenant == tenant.id_tenant)
    )
    if res.scalar_one_or_none():
        print("  [OK] Taller ya existe para el usuario taller")
        return

    taller = Taller(
        id_tenant=tenant.id_tenant,
        id_usuario=usuario.id_usuario,
        razon_social="Taller Principal S.A.",
        nombre_comercial="Taller EmergenciaVehicular",
        nit="1234567",
        telefono_atencion="70000001",
        email_atencion=usuario.email,
        direccion="Av. Principal 123",
        referencia="Cerca del parque central",
        latitud=Decimal("-16.5000000"),
        longitud=Decimal("-68.1500000"),
        capacidad_maxima=5,
        acepta_remolque=True,
        estado_registro=EstadoTallerEnum.APROBADO,
    )
    db.add(taller)
    await db.flush()
    print(f"  [+] Taller creado (id={taller.id_taller})")


async def seed_cliente(db, tenant: Tenant, usuario: Usuario) -> None:
    res = await db.execute(
        select(Cliente).where(Cliente.id_usuario == usuario.id_usuario, Cliente.id_tenant == tenant.id_tenant)
    )
    if res.scalar_one_or_none():
        print("  [OK] Perfil Cliente ya existe")
        return

    cliente = Cliente(
        id_tenant=tenant.id_tenant,
        id_usuario=usuario.id_usuario,
        ci="12345678",
        direccion="Calle Prueba 456",
        referencia="Zona Sur",
    )
    db.add(cliente)
    await db.flush()
    print(f"  [+] Perfil Cliente creado (id={cliente.id_cliente})")


PLANES_DATA = [
    {
        "slug": "demo",
        "nombre": "Demo",
        "descripcion": "Plan gratuito para talleres que quieren probar la plataforma.",
        "precio": Decimal("0.00"),
        "max_incidentes_mes": 5,
        "max_tecnicos": 2,
        "max_usuarios": 3,
        "tiene_ia": False,
        "tiene_reportes_avanzados": False,
        "tiene_soporte_prioritario": False,
        "tiene_notificaciones_push": True,
        "orden": 1,
    },
    {
        "slug": "basico",
        "nombre": "Básico",
        "descripcion": "Plan para talleres pequeños con operación habitual.",
        "precio": Decimal("99.00"),
        "max_incidentes_mes": 30,
        "max_tecnicos": 5,
        "max_usuarios": 10,
        "tiene_ia": True,
        "tiene_reportes_avanzados": False,
        "tiene_soporte_prioritario": False,
        "tiene_notificaciones_push": True,
        "orden": 2,
    },
    {
        "slug": "pro",
        "nombre": "Pro",
        "descripcion": "Plan avanzado para talleres con operación completa y soporte prioritario.",
        "precio": Decimal("199.00"),
        "max_incidentes_mes": 0,
        "max_tecnicos": 0,
        "max_usuarios": 0,
        "tiene_ia": True,
        "tiene_reportes_avanzados": True,
        "tiene_soporte_prioritario": True,
        "tiene_notificaciones_push": True,
        "orden": 3,
    },
]


async def seed_planes(db) -> dict[str, Plan]:
    planes: dict[str, Plan] = {}
    for data in PLANES_DATA:
        res = await db.execute(select(Plan).where(Plan.slug == data["slug"]))
        plan = res.scalar_one_or_none()
        if plan:
            for k, v in data.items():
                setattr(plan, k, v)
            print(f"  [OK] Plan actualizado: {data['nombre']}")
        else:
            plan = Plan(**data, estado="ACTIVO", moneda="BOB")
            db.add(plan)
            await db.flush()
            print(f"  [+] Plan creado: {data['nombre']} (id={plan.id_plan})")
        planes[data["slug"]] = plan
    return planes


async def seed_superadmin(db) -> None:
    res = await db.execute(select(SuperAdmin).where(SuperAdmin.email == "superadmin@emergencia.com"))
    sa = res.scalar_one_or_none()
    if sa:
        print("  [OK] SuperAdmin ya existe")
        return
    sa = SuperAdmin(
        email="superadmin@emergencia.com",
        password_hash=hash_password("SuperAdmin1234"),
        nombre="Super Admin",
        activo=True,
    )
    db.add(sa)
    await db.flush()
    print(f"  [+] SuperAdmin creado (id={sa.id_superadmin})")


async def seed_suscripcion(db, tenant: Tenant, plan: Plan) -> None:
    res = await db.execute(
        select(TenantSuscripcion).where(
            TenantSuscripcion.id_tenant == tenant.id_tenant,
            TenantSuscripcion.estado == "ACTIVO",
        )
    )
    if res.scalar_one_or_none():
        print(f"  [OK] Suscripción activa ya existe para {tenant.nombre}")
        return
    sus = TenantSuscripcion(
        id_tenant=tenant.id_tenant,
        id_plan=plan.id_plan,
        estado="ACTIVO",
        es_trial=(plan.precio == 0),
    )
    db.add(sus)
    await db.flush()
    print(f"  [+] Suscripción creada: {tenant.nombre} → Plan {plan.nombre}")


async def main() -> None:
    print("\n=== Seed Local — EmergenciaVehicular ===\n")
    async with AsyncSessionLocal() as db:
        print("Planes:")
        planes = await seed_planes(db)

        print("\nTenant y usuarios:")
        tenant = await get_or_create_tenant(db)

        usuarios_creados: dict[str, Usuario] = {}
        for data in USUARIOS:
            u = await seed_usuario(db, tenant, data)
            usuarios_creados[data["rol"]] = u

        print()
        await seed_taller(db, tenant, usuarios_creados["TALLER"])
        await seed_cliente(db, tenant, usuarios_creados["CLIENTE"])

        print("\nSuscripción:")
        await seed_suscripcion(db, tenant, planes["demo"])

        print("\nSuperAdmin:")
        await seed_superadmin(db)

        await db.commit()

    print("\n=== Seed completado ===")
    print(f"\nTenant: {TENANT_NOMBRE}  (slug: {TENANT_SLUG})")
    print("\nCredenciales de acceso:")
    for d in USUARIOS:
        print(f"  {d['rol']:<15}  {d['email']:<30}  {d['password']}")
    print(f"  {'SUPERADMIN':<15}  {'superadmin@emergencia.com':<30}  SuperAdmin1234")
    print()


if __name__ == "__main__":
    asyncio.run(main())
