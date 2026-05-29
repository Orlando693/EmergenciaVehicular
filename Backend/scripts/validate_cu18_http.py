import asyncio
import base64
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

import websockets


BASE_URL = "http://127.0.0.1:8018"
WS_URL = "ws://127.0.0.1:8018"
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


async def assert_ws_initial_snapshot(token: str, id_incidente: int) -> None:
    token_q = urllib.parse.quote(token, safe="")
    async with websockets.connect(f"{WS_URL}/atencion-tiempo-real/{id_incidente}/ws?token={token_q}") as ws:
        raw = await asyncio.wait_for(ws.recv(), timeout=10)
        payload = json.loads(raw)
        assert payload["tipo"] == "SEGUIMIENTO_INICIAL", payload
        assert payload["data"]["incidente"]["id_incidente"] == id_incidente, payload


async def main() -> None:
    cliente_a = login("cliente.a@test.com")
    cliente_b = login("cliente.b@test.com")
    taller_a = login("taller.a@test.com")
    taller_b = login("taller.b@test.com")

    token_cliente_a = cliente_a["access_token"]
    token_cliente_b = cliente_b["access_token"]
    token_taller_a = taller_a["access_token"]
    token_taller_b = taller_b["access_token"]

    assert jwt_payload(token_cliente_a)["id_tenant"] == cliente_a["id_tenant"]
    assert jwt_payload(token_taller_a)["id_tenant"] == taller_a["id_tenant"]
    assert cliente_a["id_tenant"] != cliente_b["id_tenant"]

    incidente_a = 8
    incidente_b = 9

    status, seguimiento_cliente_a = request("GET", f"/atencion-tiempo-real/{incidente_a}", token_cliente_a)
    assert status == 200, seguimiento_cliente_a
    assert seguimiento_cliente_a["incidente"]["id_incidente"] == incidente_a

    status, seguimiento_taller_a = request("GET", f"/atencion-tiempo-real/{incidente_a}", token_taller_a)
    assert status == 200, seguimiento_taller_a
    assert seguimiento_taller_a["incidente"]["id_incidente"] == incidente_a

    status, cross_cliente_b = request("GET", f"/atencion-tiempo-real/{incidente_a}", token_cliente_b)
    assert status in (403, 404), f"Cliente B pudo ver incidente A: {status} {cross_cliente_b}"

    status, cross_taller_b = request("POST", f"/atencion-tiempo-real/{incidente_a}/rechazar", token_taller_b, {"observacion": "Intento cruzado"})
    assert status in (403, 404), f"Taller B pudo modificar incidente A: {status} {cross_taller_b}"

    status, aceptado = request("POST", f"/atencion-tiempo-real/{incidente_a}/aceptar", token_taller_a, {"observacion": "Validacion CU18"})
    assert status == 200, aceptado
    assert aceptado["estado"] == "EN_PROCESO"

    status, actualizado = request(
        "PATCH",
        f"/atencion-tiempo-real/{incidente_a}/estado",
        token_taller_a,
        {"estado": "RESUELTO", "observacion": "Validacion CU18 resuelta"},
    )
    assert status == 200, actualizado
    assert actualizado["estado"] == "RESUELTO"

    status, cross_taller_a = request("GET", f"/atencion-tiempo-real/{incidente_b}", token_taller_a)
    assert status in (403, 404), f"Taller A pudo ver incidente B: {status} {cross_taller_a}"

    await assert_ws_initial_snapshot(token_cliente_a, incidente_a)

    print("OK CU18 atencion en tiempo real")
    print(f"Tenant A id_tenant={cliente_a['id_tenant']} incidente={incidente_a}")
    print(f"Tenant B id_tenant={cliente_b['id_tenant']} incidente={incidente_b}")
    print("Aislamiento validado: Cliente/Taller B no acceden a incidente A; Taller A no accede a incidente B")
    print("WebSocket validado: seguimiento inicial recibido para Tenant A")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
