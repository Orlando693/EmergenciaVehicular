import base64
import json
import sys
import time
import urllib.error
import urllib.request


BASE_URL = "http://127.0.0.1:8019"
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
        with urllib.request.urlopen(req, timeout=20) as resp:
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


def main() -> None:
    cliente_a = login("cliente.a@test.com")
    cliente_b = login("cliente.b@test.com")
    token_a = cliente_a["access_token"]
    token_b = cliente_b["access_token"]

    assert jwt_payload(token_a)["id_tenant"] == cliente_a["id_tenant"]
    assert cliente_a["id_tenant"] != cliente_b["id_tenant"]

    client_sync_id = f"cu19-test-{int(time.time())}"
    payload = {
        "client_sync_id": client_sync_id,
        "emergencia": {
            "id_vehiculo": 3,
            "descripcion": "Prueba CU19: vehiculo no arranca tras corte electrico.",
            "ubicacion_lat": -16.5,
            "ubicacion_lng": -68.15,
            "direccion": "Zona prueba CU19",
        },
    }

    status, first = request("POST", "/atencion-tiempo-real/sincronizar-emergencia-offline", token_a, payload)
    assert status == 200, first
    assert first["estado_sync"] == "SINCRONIZADA", first
    assert first["id_incidente"], first

    status, second = request("POST", "/atencion-tiempo-real/sincronizar-emergencia-offline", token_a, payload)
    assert status == 200, second
    assert second["estado_sync"] == "SINCRONIZADA", second
    assert second["id_incidente"] == first["id_incidente"], (first, second)
    assert "previamente" in second["mensaje"].lower(), second

    status, estado = request("GET", f"/atencion-tiempo-real/sincronizaciones/{client_sync_id}", token_a)
    assert status == 200, estado
    assert estado["id_incidente"] == first["id_incidente"], estado

    status, cross = request("GET", f"/atencion-tiempo-real/sincronizaciones/{client_sync_id}", token_b)
    assert status == 404, f"Tenant B pudo consultar sync de Tenant A: {status} {cross}"

    print("OK CU19 sincronizacion offline")
    print(f"Tenant A id_tenant={cliente_a['id_tenant']} client_sync_id={client_sync_id} incidente={first['id_incidente']}")
    print(f"Tenant B id_tenant={cliente_b['id_tenant']} no puede ver la sincronizacion de Tenant A")
    print("Idempotencia validada: el reintento devolvio el mismo incidente sin duplicar")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
