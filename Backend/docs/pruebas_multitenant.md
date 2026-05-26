# Pruebas Multi-Tenant CU27

## Preparacion

```powershell
cd Backend
$env:DEBUG='false'
.\venv\Scripts\alembic.exe upgrade head
.\venv\Scripts\python.exe scripts\seed_multitenant_test.py
.\venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000
```

En otra terminal:

```powershell
cd Backend
$env:DEBUG='false'
.\venv\Scripts\python.exe scripts\check_multitenant_status.py
.\venv\Scripts\python.exe scripts\validate_multitenant_http.py
```

## Usuarios De Prueba

Todos usan password `Test1234`.

Tenant A: Auxilio Norte (`auxilio-norte`)

- `admin.a@test.com`
- `taller.a@test.com`
- `cliente.a@test.com`

Tenant B: Mecanicos Express (`mecanicos-express`)

- `admin.b@test.com`
- `taller.b@test.com`
- `cliente.b@test.com`

## Validaciones

1. Login con `admin.a@test.com`.
2. Decodificar JWT y confirmar `id_tenant` de Tenant A.
3. `GET /incidentes` con token de Tenant A debe devolver solo incidentes de Tenant A.
4. `GET /talleres` con token de Tenant A debe devolver solo talleres de Tenant A.
5. `GET /vehiculos` con token de `cliente.a@test.com` debe devolver solo vehiculos de Tenant A.
6. `GET /incidentes/{id_incidente_b}` con token de Tenant A debe devolver `403` o `404`.
7. Login con `admin.b@test.com`.
8. Confirmar que Tenant B no ve incidentes, talleres ni vehiculos de Tenant A.
9. Validar que `GET /reportes/resumen`, `GET /pagos/admin/todos`, `GET /notificaciones` y `GET /bitacora` responden filtrados por tenant.

## Resultado Esperado Automatizado

`scripts/validate_multitenant_http.py` debe imprimir:

```text
OK aislamiento multi-tenant por HTTP
Tenant A id_tenant=<id> incidentes=[...] vehiculos=[...]
Tenant B id_tenant=<id> incidentes=[...] vehiculos=[...]
Pagos A=[...] Pagos B=[...]
Notificaciones A=[...] Notificaciones B=[...]
Bitacora A=[...] Bitacora B=[...]
Acceso cruzado A -> incidente B <id>: HTTP 404
```

El codigo `404` tambien es valido para aislamiento porque el recurso de otro tenant no debe ser visible por URL directa.
