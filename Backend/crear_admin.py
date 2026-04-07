"""
Setup completo: crea tablas, roles, permisos y usuario administrador.
No requiere ejecutar nada en pgAdmin.
"""
import sys, asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, text

from app.config import settings
from app.database import Base
from app.models import *  # noqa – registra todos los modelos
from app.models.usuario import Usuario, Rol, Permiso, RolPermiso, UsuarioRol
from app.core.security import hash_password

# ─────────────────────────────────────────────────────────
# Datos semilla (equivalente al SQL de BaseDeDatos.doc)
# ─────────────────────────────────────────────────────────

ROLES = [
    {"nombre": "CLIENTE",        "descripcion": "Usuario móvil que reporta incidentes y realiza pagos"},
    {"nombre": "TALLER",         "descripcion": "Proveedor de asistencia vehicular y gestión de técnicos"},
    {"nombre": "ADMINISTRADOR",  "descripcion": "Gestiona roles, bitácora, reportes y supervisión general"},
]

PERMISOS = [
    ("auth.login",                   "Iniciar sesión en el sistema"),
    ("usuarios.registrar",           "Registrar usuarios clientes"),
    ("usuarios.perfil",              "Gestionar perfil del usuario"),
    ("roles.gestionar",              "Gestionar roles y permisos"),
    ("vehiculos.gestionar",          "Registrar y administrar vehículos"),
    ("incidentes.reportar",          "Registrar incidentes y evidencias"),
    ("incidentes.consultar_historial","Consultar historial de incidentes"),
    ("talleres.gestionar",           "Registrar y gestionar talleres"),
    ("tecnicos.gestionar",           "Registrar técnicos y disponibilidad"),
    ("solicitudes.visualizar",       "Visualizar solicitudes disponibles"),
    ("asignacion.ejecutar",          "Asignar taller adecuado"),
    ("servicios.estado",             "Gestionar estado e historial del servicio"),
    ("notificaciones.gestionar",     "Gestionar notificaciones y alertas"),
    ("mensajes.gestionar",           "Comunicación usuario-taller"),
    ("pagos.gestionar",              "Gestionar pagos"),
    ("bitacora.gestionar",           "Gestionar bitácora"),
    ("reportes.generar",             "Generar reportes"),
]

ROL_PERMISOS = {
    "CLIENTE": [
        "auth.login", "usuarios.registrar", "usuarios.perfil",
        "vehiculos.gestionar", "incidentes.reportar",
        "incidentes.consultar_historial", "notificaciones.gestionar",
        "mensajes.gestionar", "pagos.gestionar",
    ],
    "TALLER": [
        "auth.login", "talleres.gestionar", "tecnicos.gestionar",
        "solicitudes.visualizar", "servicios.estado",
        "notificaciones.gestionar", "mensajes.gestionar", "pagos.gestionar",
    ],
    "ADMINISTRADOR": [
        "auth.login", "roles.gestionar", "asignacion.ejecutar",
        "bitacora.gestionar", "reportes.generar",
        "notificaciones.gestionar", "incidentes.consultar_historial",
    ],
}

# ─────────────────────────────────────────────────────────

async def setup():
    print(f"Conectando a: {settings.DATABASE_URL}\n")

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    # 1) Crear tipos ENUM en PostgreSQL (necesario antes de create_all)
    enum_defs = [
        ("estado_usuario_enum",        "'ACTIVO','INACTIVO','BLOQUEADO'"),
        ("estado_taller_enum",         "'PENDIENTE','APROBADO','SUSPENDIDO','RECHAZADO'"),
        ("estado_tecnico_enum",        "'DISPONIBLE','OCUPADO','INACTIVO'"),
        ("tipo_incidente_enum",        "'BATERIA','LLANTA','CHOQUE','MOTOR','LLAVES','SOBRECALENTAMIENTO','OTRO','INCIERTO'"),
        ("prioridad_incidente_enum",   "'ALTA','MEDIA','BAJA'"),
        ("estado_incidente_enum",      "'PENDIENTE','EN_EVALUACION','ASIGNADO','EN_PROCESO','ATENDIDO','CANCELADO'"),
        ("tipo_evidencia_enum",        "'IMAGEN','AUDIO','TEXTO'"),
        ("estado_ia_enum",             "'PENDIENTE','PROCESADO','REQUIERE_MAS_INFO','ERROR'"),
        ("estado_solicitud_taller_enum","'PENDIENTE','ACEPTADA','RECHAZADA','EXPIRADA','CANCELADA'"),
        ("estado_asignacion_enum",     "'ACTIVA','FINALIZADA','REASIGNADA','CANCELADA'"),
        ("tipo_notificacion_enum",     "'NUEVA_SOLICITUD','CAMBIO_ESTADO','ASIGNACION','PAGO','ALERTA','MENSAJE'"),
        ("plataforma_dispositivo_enum","'ANDROID','IOS','WEB'"),
        ("tipo_mensaje_enum",          "'TEXTO','IMAGEN','AUDIO','SISTEMA'"),
        ("metodo_pago_enum",           "'TARJETA','QR','TRANSFERENCIA','EFECTIVO','OTRO'"),
        ("estado_pago_enum",           "'PENDIENTE','PAGADO','FALLIDO','REEMBOLSADO','ANULADO'"),
        ("estado_comision_enum",       "'PENDIENTE','PAGADA','ANULADA'"),
    ]

    async with engine.begin() as conn:
        for name, values in enum_defs:
            await conn.execute(text(
                f"DO $$ BEGIN "
                f"IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{name}') THEN "
                f"CREATE TYPE {name} AS ENUM ({values}); "
                f"END IF; END $$;"
            ))
        print("[OK] Tipos ENUM verificados/creados")

        await conn.run_sync(Base.metadata.create_all)
        print("[OK] Tablas creadas/verificadas")

    # 2) Insertar roles
    async with Session() as db:
        for r in ROLES:
            existe = await db.execute(select(Rol).where(Rol.nombre == r["nombre"]))
            if not existe.scalar_one_or_none():
                db.add(Rol(nombre=r["nombre"], descripcion=r["descripcion"]))
        await db.commit()
        print("[OK] Roles verificados/creados")

    # 3) Insertar permisos
    async with Session() as db:
        for codigo, desc in PERMISOS:
            existe = await db.execute(select(Permiso).where(Permiso.codigo == codigo))
            if not existe.scalar_one_or_none():
                db.add(Permiso(codigo=codigo, descripcion=desc))
        await db.commit()
        print("[OK] Permisos verificados/creados")

    # 4) Asignar permisos a roles
    async with Session() as db:
        for rol_nombre, codigos in ROL_PERMISOS.items():
            rol = (await db.execute(select(Rol).where(Rol.nombre == rol_nombre))).scalar_one_or_none()
            if not rol:
                continue
            for codigo in codigos:
                perm = (await db.execute(select(Permiso).where(Permiso.codigo == codigo))).scalar_one_or_none()
                if not perm:
                    continue
                existe = (await db.execute(
                    select(RolPermiso).where(RolPermiso.id_rol == rol.id_rol, RolPermiso.id_permiso == perm.id_permiso)
                )).scalar_one_or_none()
                if not existe:
                    db.add(RolPermiso(id_rol=rol.id_rol, id_permiso=perm.id_permiso))
        await db.commit()
        print("[OK] Permisos asignados a roles")

    # 5) Crear usuario administrador
    async with Session() as db:
        existe = (await db.execute(select(Usuario).where(Usuario.email == "admin@emergencia.com"))).scalar_one_or_none()
        if existe:
            print("\n[INFO] El administrador ya existe.")
        else:
            rol_admin = (await db.execute(select(Rol).where(Rol.nombre == "ADMINISTRADOR"))).scalar_one()
            admin = Usuario(
                nombres="Admin",
                apellidos="Sistema",
                email="admin@emergencia.com",
                password_hash=hash_password("Admin1234"),
            )
            db.add(admin)
            await db.flush()
            db.add(UsuarioRol(id_usuario=admin.id_usuario, id_rol=rol_admin.id_rol))
            await db.commit()
            print("\n[OK] Administrador creado")

    await engine.dispose()

    print()
    print("=" * 40)
    print("CREDENCIALES DE ACCESO:")
    print("  Email:    admin@emergencia.com")
    print("  Password: Admin1234")
    print("=" * 40)
    print()
    print("Ahora levanta el backend:")
    print("  uvicorn app.main:app --reload --port 8000 --loop asyncio")

if __name__ == "__main__":
    asyncio.run(setup())
