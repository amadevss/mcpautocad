import json
import threading
import urllib.error
import urllib.request

import pytest

from mcpautocad import actualizaciones, configuracion, panel, registrar


@pytest.fixture
def url():
    servidor = panel.crear_servidor(0)
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    yield f"http://127.0.0.1:{servidor.server_address[1]}"
    servidor.shutdown()
    servidor.server_close()


def pedir(url, ruta, cuerpo=None, cabeceras=None):
    datos = None if cuerpo is None else json.dumps(cuerpo).encode()
    req = urllib.request.Request(url + ruta, data=datos, headers={
        **({"Content-Type": "application/json"} if cuerpo is not None else {}), **(cabeceras or {})})
    with urllib.request.urlopen(req, timeout=5) as r:
        return r.status, r.read()


def test_pagina_y_estado(url):
    codigo, html = pedir(url, "/")
    assert codigo == 200 and "Panel MCP AutoCAD".encode() in html
    codigo, png = pedir(url, "/icono.png")
    assert codigo == 200 and png.startswith(b"\x89PNG")
    estado = json.loads(pedir(url, "/api/estado")[1])
    assert estado["config"] == configuracion.POR_DEFECTO
    assert estado["claude"]["registrado"] is False
    assert estado["maximo"]["herramientas"] == 248


def test_guardar_avisa_reinicio(url):
    nueva = {"modo": "busqueda", "paquetes": ["pid"], "3d": False}
    r = json.loads(pedir(url, "/api/guardar", {"config": nueva})[1])
    assert "Reinicia Claude Desktop" in r["mensaje"]
    assert configuracion.cargar()["modo"] == "busqueda"
    assert r["estimacion"]["herramientas"] == 3


def test_registrar_y_quitar(url):
    r = json.loads(pedir(url, "/api/registrar", {})[1])
    assert r["claude"]["registrado"] is True
    assert registrar.esta_registrado(registrar.rutas_claude()[0])
    r = json.loads(pedir(url, "/api/quitar", {})[1])
    assert r["claude"]["registrado"] is False


def test_rechaza_peticiones_de_otras_webs(url):
    with pytest.raises(urllib.error.HTTPError) as e:
        pedir(url, "/api/guardar", {"config": {}}, {"Origin": "https://malicioso.example"})
    assert e.value.code == 403
    with pytest.raises(urllib.error.HTTPError) as e:  # formulario, no JSON
        req = urllib.request.Request(url + "/api/registrar", data=b"a=1",
                                     headers={"Content-Type": "application/x-www-form-urlencoded"})
        urllib.request.urlopen(req, timeout=5)
    assert e.value.code == 403
    with pytest.raises(urllib.error.HTTPError) as e:  # DNS rebinding
        pedir(url, "/api/estado", cabeceras={"Host": "malicioso.example"})
    assert e.value.code == 403
    assert not registrar.rutas_claude()[0].exists()


def test_lista_de_herramientas_y_guardar_apagadas(url):
    r = json.loads(pedir(url, "/api/herramientas", {"config": {"modo": "ligero"}})[1])
    assert len(r["herramientas"]) == 248
    cfg = {"modo": "ligero", "desactivadas": ["entity_create_line"]}
    r = json.loads(pedir(url, "/api/guardar", {"config": cfg})[1])
    assert r["config"]["desactivadas"] == ["entity_create_line"]
    assert r["estimacion"]["herramientas"] == 65


def test_probar_conexion(url):
    configuracion.guardar({"motor": "ezdxf"})
    r = json.loads(pedir(url, "/api/probar", {})[1])
    assert r["ok"] is True and r["motor"] == "ezdxf"


def test_aviso_de_version_sin_internet(url, monkeypatch):
    actualizaciones._CACHE.clear()

    def sin_red(timeout):
        raise OSError("sin internet")

    monkeypatch.setattr(actualizaciones, "_ultimo_release", sin_red)
    r = json.loads(pedir(url, "/api/version")[1])
    assert r["hay_nueva"] is False and r["actual"]
