import base64
import json
import sys
import urllib.error
import urllib.request


BASE_URL = "http://127.0.0.1:8020"
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
    taller_a = login("taller.a@test.com")
    taller_b = login("taller.b@test.com")

    token_cliente_a = cliente_a["access_token"]
    token_cliente_b = cliente_b["access_token"]
    token_taller_a = taller_a["access_token"]
    token_taller_b = taller_b["access_token"]

    assert jwt_payload(token_cliente_a)["id_tenant"] == cliente_a["id_tenant"]
    assert cliente_a["id_tenant"] != cliente_b["id_tenant"]

    status, incidentes_a = request("GET", "/incidentes", token_cliente_a)
    assert status == 200, incidentes_a
    incidente = next((item for item in incidentes_a if item.get("id_taller")), None)
    assert incidente, f"Tenant A no tiene incidente con taller asignado: {incidentes_a}"
    id_incidente = incidente["id_incidente"]

    status, solicitud = request(
        "POST",
        "/atencion-tiempo-real/cotizaciones/solicitar",
        token_cliente_a,
        {
            "id_incidente": id_incidente,
            "descripcion_solicitud": "Cotizar reparacion completa del problema reportado.",
        },
    )
    assert status == 200, solicitud
    assert solicitud["id_incidente"] == id_incidente
    id_cotizacion = solicitud["id_cotizacion"]

    status, solicitud_repetida = request(
        "POST",
        "/atencion-tiempo-real/cotizaciones/solicitar",
        token_cliente_a,
        {
            "id_incidente": id_incidente,
            "descripcion_solicitud": "Reintento de solicitud no debe duplicar.",
        },
    )
    assert status == 200, solicitud_repetida
    assert solicitud_repetida["id_cotizacion"] == id_cotizacion, (solicitud, solicitud_repetida)

    status, respuesta = request(
        "PATCH",
        f"/atencion-tiempo-real/cotizaciones/{id_cotizacion}/responder",
        token_taller_a,
        {
            "precio_estimado": "350.50",
            "detalle_danio": "Falla electrica en sistema de arranque y revision de bateria.",
            "condiciones_servicio": "Incluye diagnostico, mano de obra y repuestos basicos sujetos a disponibilidad.",
            "tiempo_estimado": "2 horas",
        },
    )
    assert status == 200, respuesta
    assert respuesta["estado"] == "RESPONDIDA", respuesta
    assert respuesta["precio_estimado"] == "350.50", respuesta

    status, detalle_cliente = request("GET", f"/atencion-tiempo-real/cotizaciones/{id_cotizacion}", token_cliente_a)
    assert status == 200, detalle_cliente
    assert detalle_cliente["id_cotizacion"] == id_cotizacion

    status, lista_taller = request("GET", "/atencion-tiempo-real/cotizaciones", token_taller_a)
    assert status == 200, lista_taller
    assert any(item["id_cotizacion"] == id_cotizacion for item in lista_taller), lista_taller

    status, cross_cliente = request("GET", f"/atencion-tiempo-real/cotizaciones/{id_cotizacion}", token_cliente_b)
    assert status == 404, f"Tenant B pudo ver cotizacion Tenant A: {status} {cross_cliente}"

    status, cross_taller = request(
        "PATCH",
        f"/atencion-tiempo-real/cotizaciones/{id_cotizacion}/responder",
        token_taller_b,
        {
            "precio_estimado": "999.99",
            "detalle_danio": "Intento cruzado",
            "condiciones_servicio": "No deberia permitirse",
            "tiempo_estimado": "1 hora",
        },
    )
    assert status == 404, f"Taller B pudo responder cotizacion Tenant A: {status} {cross_taller}"

    print("OK CU20 cotizaciones de reparacion")
    print(f"Tenant A id_tenant={cliente_a['id_tenant']} incidente={id_incidente} cotizacion={id_cotizacion}")
    print(f"Tenant B id_tenant={cliente_b['id_tenant']} no puede ver ni responder cotizacion de Tenant A")
    print("Solicitud repetida validada: devolvio la misma cotizacion sin duplicar")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
