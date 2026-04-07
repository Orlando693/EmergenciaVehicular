"""Diagnóstico y setup de PostgreSQL para EmergenciaVehicular."""
import sys, re, subprocess, io
from pathlib import Path

# Forzar UTF-8 en stdout para Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

try:
    import psycopg2
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary", "-q"])
    import psycopg2

# ── Leer .env ─────────────────────────────────────────────
env_path = Path(__file__).parent / ".env"
config = {}
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            config[k.strip()] = v.strip()

db_url = config.get("DATABASE_URL", "")
m = re.match(r"postgresql\+asyncpg://([^:]+):([^@]*)@([^:/]+):?(\d*)/(.+)", db_url)
if not m:
    print(f"ERROR: No se pudo parsear DATABASE_URL: {db_url}")
    sys.exit(1)

user, password, host, port, dbname = m.groups()
port = int(port or "5432")

print("=" * 52)
print("Diagnostico PostgreSQL - EmergenciaVehicular")
print("=" * 52)
print(f"  Host:    {host}:{port}")
print(f"  Usuario: {user}")
print(f"  BD:      {dbname}")
print()

def conectar(db="postgres"):
    return psycopg2.connect(
        host=host, port=port, user=user, password=password,
        dbname=db, connect_timeout=5,
        options="-c client_encoding=UTF8",
    )

# ── Test 1: PostgreSQL activo ─────────────────────────────
try:
    conn = conectar()
    conn.close()
    print("[OK] PostgreSQL corriendo - contrasena correcta")
except psycopg2.OperationalError as e:
    print(f"[ERROR] No se pudo conectar a PostgreSQL:\n  {e}")
    print()
    print("Posibles causas:")
    print("  1. PostgreSQL no esta activo")
    print("     -> Abre 'Servicios' (Win+R -> services.msc)")
    print("     -> Busca 'postgresql-x64-XX' y arráncalo")
    print("  2. Contrasena incorrecta en .env")
    sys.exit(1)

# ── Test 2: BD existe, si no, crearla ────────────────────
db_existe = False
try:
    conn = conectar(dbname)
    conn.close()
    db_existe = True
    print(f"[OK] Base de datos '{dbname}' existe")
except Exception:
    print(f"[INFO] Base de datos '{dbname}' NO existe - creandola ahora...")
    try:
        conn = conectar()
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE \"{dbname}\" ENCODING 'UTF8';")
        conn.close()
        print(f"[OK] Base de datos '{dbname}' creada exitosamente")
        db_existe = True
    except Exception as e2:
        print(f"[ERROR] No se pudo crear la BD: {e2}")
        sys.exit(1)

# ── Test 3: Roles semilla ─────────────────────────────────
roles_ok = False
try:
    conn = conectar(dbname)
    with conn.cursor() as cur:
        cur.execute("SELECT nombre FROM roles LIMIT 5")
        roles = [r[0] for r in cur.fetchall()]
    conn.close()
    print(f"[OK] Roles encontrados: {roles}")
    roles_ok = True
except Exception:
    print("[AVISO] Tabla 'roles' no existe aun")
    print("  -> Ejecuta el SQL de BaseDeDatos.doc en pgAdmin")

# ── Resumen ───────────────────────────────────────────────
print()
print("=" * 52)
if roles_ok:
    print("TODO LISTO. Siguiente comando:")
    print("   python crear_admin.py")
else:
    print("SIGUIENTE PASO:")
    print("  1. Abre pgAdmin")
    print(f"  2. Conectate a la BD '{dbname}'")
    print("  3. Abre Query Tool")
    print("  4. Pega y ejecuta TODO el contenido de BaseDeDatos.doc")
    print("  5. Luego ejecuta: python crear_admin.py")
print("=" * 52)
