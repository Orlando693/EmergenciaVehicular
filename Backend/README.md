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

## Flujo básico de prueba

```
1. POST /usuarios  →  { email, password, nombres, apellidos, rol: "ADMINISTRADOR" }
2. POST /auth/login  →  { access_token }
3. Usar el token en Authorization: Bearer <token>
4. POST /talleres  →  registrar un taller
5. PATCH /talleres/{id}/estado  →  { estado_registro: "APROBADO" }
6. POST /talleres/{id}/tecnicos  →  agregar técnicos
```
