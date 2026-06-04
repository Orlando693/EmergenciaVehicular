import base64
import json
import sys
import urllib.error
import urllib.request


BASE_URL = "http://127.0.0.1:8000"
PASSWORD = "Test1234"


def request(method: str, path: str, token: str | None = None, body: dict | None = None) -> tuple[int, dict | list | str]:
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(f"{BASE_URL}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = raw
        return exc.code, payload


def login(email: str) -> dict:
    status, payload = request("POST", "/auth/login", body={"email": email, "password": PASSWORD})
    assert status == 200, f"Login fallo para {email}: {status} {payload}"
    return payload


def jwt_payload(token: str) -> dict:
    part = token.split(".")[1]
    part += "=" * (-len(part) % 4)
    return json.loads(base64.urlsafe_b64decode(part.encode("ascii")))


def ids(items: list[dict], key: str) -> set[int]:
    return {int(item[key]) for item in items}


def main() -> None:
    admin_a = login("admin.a@test.com")
    admin_b = login("admin.b@test.com")
    cliente_a = login("cliente.a@test.com")
    cliente_b = login("cliente.b@test.com")

    token_admin_a = admin_a["access_token"]
    token_admin_b = admin_b["access_token"]
    token_cliente_a = cliente_a["access_token"]
    token_cliente_b = cliente_b["access_token"]

    payload_a = jwt_payload(token_admin_a)
    payload_b = jwt_payload(token_admin_b)
    assert payload_a["id_tenant"] == admin_a["id_tenant"]
    assert payload_b["id_tenant"] == admin_b["id_tenant"]
    assert admin_a["id_tenant"] != admin_b["id_tenant"]

    status, inc_a = request("GET", "/incidentes", token_admin_a)
    assert status == 200, inc_a
    status, inc_b = request("GET", "/incidentes", token_admin_b)
    assert status == 200, inc_b
    inc_ids_a = ids(inc_a, "id_incidente")
    inc_ids_b = ids(inc_b, "id_incidente")
    assert inc_ids_a and inc_ids_b and inc_ids_a.isdisjoint(inc_ids_b)

    status, talleres_a = request("GET", "/talleres", token_admin_a)
    assert status == 200, talleres_a
    status, talleres_b = request("GET", "/talleres", token_admin_b)
    assert status == 200, talleres_b
    assert ids(talleres_a, "id_taller").isdisjoint(ids(talleres_b, "id_taller"))

    status, vehiculos_a = request("GET", "/vehiculos", token_cliente_a)
    assert status == 200, vehiculos_a
    status, vehiculos_b = request("GET", "/vehiculos", token_cliente_b)
    assert status == 200, vehiculos_b
    assert ids(vehiculos_a, "id_vehiculo").isdisjoint(ids(vehiculos_b, "id_vehiculo"))

    status, pagos_a = request("GET", "/pagos/admin/todos", token_admin_a)
    assert status == 200, pagos_a
    status, pagos_b = request("GET", "/pagos/admin/todos", token_admin_b)
    assert status == 200, pagos_b
    assert ids(pagos_a["items"], "id_pago").isdisjoint(ids(pagos_b["items"], "id_pago"))

    status, notif_a = request("GET", "/notificaciones", token_admin_a)
    assert status == 200, notif_a
    status, notif_b = request("GET", "/notificaciones", token_admin_b)
    assert status == 200, notif_b
    assert ids(notif_a["items"], "id_notificacion").isdisjoint(ids(notif_b["items"], "id_notificacion"))

    status, bitacora_a = request("GET", "/bitacora", token_admin_a)
    assert status == 200, bitacora_a
    status, bitacora_b = request("GET", "/bitacora", token_admin_b)
    assert status == 200, bitacora_b
    assert ids(bitacora_a["items"], "id_bitacora").isdisjoint(ids(bitacora_b["items"], "id_bitacora"))

    incidente_b = next(iter(inc_ids_b))
    status, cross_inc = request("GET", f"/incidentes/{incidente_b}", token_admin_a)
    cross_inc_status = status
    assert status in (403, 404), f"Tenant A pudo ver incidente Tenant B: {status} {cross_inc}"

    vehiculo_b = next(iter(ids(vehiculos_b, "id_vehiculo")))
    status, cross_vehicle = request("GET", f"/vehiculos/{vehiculo_b}", token_cliente_a)
    assert status in (403, 404), f"Tenant A pudo ver vehiculo Tenant B: {status} {cross_vehicle}"

    for label, token in (("A", token_admin_a), ("B", token_admin_b)):
        for path in ("/reportes/resumen",):
            status, payload = request("GET", path, token)
            assert status == 200, f"{label} {path}: {status} {payload}"

    print("OK aislamiento multi-tenant por HTTP")
    print(f"Tenant A id_tenant={admin_a['id_tenant']} incidentes={sorted(inc_ids_a)} vehiculos={sorted(ids(vehiculos_a, 'id_vehiculo'))}")
    print(f"Tenant B id_tenant={admin_b['id_tenant']} incidentes={sorted(inc_ids_b)} vehiculos={sorted(ids(vehiculos_b, 'id_vehiculo'))}")
    print(f"Pagos A={sorted(ids(pagos_a['items'], 'id_pago'))} Pagos B={sorted(ids(pagos_b['items'], 'id_pago'))}")
    print(f"Notificaciones A={sorted(ids(notif_a['items'], 'id_notificacion'))} Notificaciones B={sorted(ids(notif_b['items'], 'id_notificacion'))}")
    print(f"Bitacora A={sorted(ids(bitacora_a['items'], 'id_bitacora'))} Bitacora B={sorted(ids(bitacora_b['items'], 'id_bitacora'))}")
    print(f"Acceso cruzado A -> incidente B {incidente_b}: HTTP {cross_inc_status}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
