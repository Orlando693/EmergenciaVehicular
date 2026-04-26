# EmergenciaVehicular - Backend API

FastAPI + PostgreSQL — Ciclo 1

## Casos de uso implementados

| CU  | Descripción              | Rol(es)                    |
|-----|--------------------------|----------------------------|
| CU1 | Inicio de sesión         | Todos                      |
| CU2 | Registrar usuario        | Público                    |
| CU3 | Gestionar perfil         | Usuario autenticado         |
| CU4 | Gestionar roles/permisos | ADMINISTRADOR              |
| CU7 | Registrar taller         | TALLER                     |
| CU8 | Gestionar perfil taller  | TALLER / ADMINISTRADOR     |
| CU9 | Gestionar técnicos       | TALLER                     |

## Estructura del proyecto

```
app/
├── main.py           # Punto de entrada FastAPI
├── config.py         # Variables de entorno (pydantic-settings)
├── database.py       # Engine async + Base ORM
├── models/           # Modelos SQLAlchemy (tablas)
├── schemas/          # Schemas Pydantic (request/response)
├── core/
│   ├── security.py   # JWT, hashing bcrypt
│   └── dependencies.py # get_db, get_current_user, require_roles
├── routers/          # Endpoints FastAPI
└── services/         # Lógica de negocio
alembic/              # Migraciones de base de datos
```

## Configuración

1. Copiar `.env.example` a `.env` y completar los valores:

```env
DATABASE_URL=postgresql+asyncpg://postgres:TU_PASSWORD@localhost:5432/emergencia_vehicular
SECRET_KEY=un_secreto_muy_largo_y_seguro
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

2. Crear la base de datos en PostgreSQL:

```sql
CREATE DATABASE emergencia_vehicular;
```

3. Ejecutar el SQL de `BaseDeDatos.doc` en tu cliente PostgreSQL (pgAdmin/psql)
   para crear los tipos enum, triggers y datos semilla.

## Levantar el servidor

```powershell
# Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Iniciar con recarga automática
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Endpoints principales

| Método | Ruta                                  | Descripción                        |
|--------|---------------------------------------|------------------------------------|
| POST   | /auth/login                           | Login → JWT                        |
| POST   | /usuarios                             | Registrar usuario                  |
| GET    | /usuarios/me                          | Mi perfil                          |
| PUT    | /usuarios/me                          | Actualizar perfil                  |
| POST   | /usuarios/me/cambiar-password         | Cambiar contraseña                 |
| GET    | /usuarios                             | Listar usuarios (ADMIN)            |
| PATCH  | /usuarios/{id}/estado                 | Activar/bloquear usuario (ADMIN)   |
| GET    | /roles                                | Listar roles (ADMIN)               |
| POST   | /roles                                | Crear rol (ADMIN)                  |
| PUT    | /roles/{id}/permisos                  | Asignar permisos a rol (ADMIN)     |
| POST   | /talleres                             | Registrar taller                   |
| GET    | /talleres/mi-taller                   | Ver mi taller (TALLER)             |
| PUT    | /talleres/mi-taller                   | Actualizar mi taller (TALLER)      |
| PATCH  | /talleres/{id}/estado                 | Aprobar/rechazar taller (ADMIN)    |
| POST   | /talleres/{id}/tecnicos               | Registrar técnico (TALLER)         |
| GET    | /talleres/{id}/tecnicos               | Listar técnicos del taller         |
| PUT    | /talleres/{id}/tecnicos/{id_tecnico}  | Actualizar técnico (TALLER)        |
| DELETE | /talleres/{id}/tecnicos/{id_tecnico}  | Desactivar técnico (TALLER)        |

## Documentación interactiva

- Swagger UI: http://localhost:8000/docs
- ReDoc:       http://localhost:8000/redoc

## Despliegue en Railway

### 1. Variables de entorno (en Railway → tu servicio → Variables)

| Variable | Valor |
|----------|-------|
| `DATABASE_URL` | `postgresql+asyncpg://avnadmin:TU_PASSWORD@pg-3bd64a8c-netcrow.l.aivencloud.com:10829/defaultdb` |
| `DB_SSL_REQUIRED` | `True` |
| `SECRET_KEY` | Generar con `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ALGORITHM` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` |
| `DEBUG` | `False` |
| `CORS_ORIGINS` | `https://parcial1si2.web.app` (sin `*` con credenciales) |
| `GEMINI_API_KEY` | Tu clave real de Google AI Studio |
| `UPLOAD_DIR` | `/data/uploads` (requiere Volume montado en `/data`) |

### 2. Volume persistente para imágenes/audio

Railway tiene **filesystem efímero**: cada redeploy borra el disco. Para que las
fotos y audios subidos sobrevivan:

1. En Railway → tu servicio → **Volumes** → **+ New Volume**
2. Mount path: `/data`
3. Setear `UPLOAD_DIR=/data/uploads` en Variables

Si no creas el volumen, las imágenes anteriores se perderán al reiniciar pero
el sistema seguirá funcionando para nuevas cargas.

### 3. Primer deploy: sembrar roles, permisos y admin

Tras el primer despliegue exitoso, ejecuta una sola vez (desde tu terminal local
con Railway CLI o desde la UI → Shell):

```bash
railway run python crear_admin.py
```

Esto crea: roles (`CLIENTE`, `TALLER`, `ADMINISTRADOR`), permisos, y un usuario
admin (`admin@emergencia.com` / `Admin1234`). **Cambia esa contraseña tras el
primer login.**

### 4. Healthchecks

- `GET /` → ping rápido (Railway healthcheck por defecto).
- `GET /health` → ping + verificación de la BD (`SELECT 1`).

### 5. Frontend

`Frontend/src/environments/environment.prod.ts` ya apunta a
`https://emergenciavehicular-production.up.railway.app`. Si tu URL de Railway
cambia, actualiza ese archivo y redeploya el frontend a Firebase Hosting.

## Flujo básico de prueba

```
1. POST /usuarios  →  { email, password, nombres, apellidos, rol: "ADMINISTRADOR" }
2. POST /auth/login  →  { access_token }
3. Usar el token en Authorization: Bearer <token>
4. POST /talleres  →  registrar un taller
5. PATCH /talleres/{id}/estado  →  { estado_registro: "APROBADO" }
6. POST /talleres/{id}/tecnicos  →  agregar técnicos
```
