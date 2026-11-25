"""Claude Desktop y AutoCAD como programas: abiertos, cerrar y volver a abrir Claude."""

import json
import subprocess
import urllib.request

import pytest

from mcpautocad import panel, procesos, registrar


class Simulador:
    """Hace de Windows: tasklist, taskkill, powershell y Popen."""

    def __init__(self, abiertos=("claude.exe",), app_tienda="Claude_pzs8sxrjxfjjc!Claude"):
        self.abiertos = set(abiertos)
        self.app_tienda = app_tienda
        self.lanzados = []

    def run(self, args, **kw):
        if args[0] == "tasklist":
            nombre = args[2].split("eq ")[1]
            return subprocess.CompletedProcess(args, 0, stdout=nombre if nombre in self.abiertos else "", stderr="")
        if args[0] == "taskkill":
            self.abiertos.discard("claude.exe")
            return subprocess.CompletedProcess(args, 0, stdout="", stderr="")
        if args[0] == "powershell":
            return subprocess.CompletedProcess(args, 0, stdout=self.app_tienda + "\n", stderr="")
        raise AssertionError(args)

    def popen(self, args, **kw):
        self.lanzados.append(args)


@pytest.fixture
def windows(monkeypatch, tmp_path):
    sim = Simulador()
    monkeypatch.setattr(procesos.sys, "platform", "win32")
    monkeypatch.setattr(procesos.subprocess, "run", sim.run)
    monkeypatch.setattr(procesos.subprocess, "Popen", sim.popen)
    monkeypatch.setattr(procesos.time, "sleep", lambda s: None)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "Local"))
    return sim


def test_fuera_de_windows_no_se_sabe(monkeypatch):
    monkeypatch.setattr(procesos.sys, "platform", "linux")
    assert procesos.autocad_abierto() is None
    assert procesos.cerrar_claude() is False
    assert procesos.comando_abrir_claude() is None


def test_detecta_programas_abiertos(windows):
    assert procesos.claude_abierto() is True
    assert procesos.autocad_abierto() is False
    windows.abiertos.add("acad.exe")
    assert procesos.autocad_abierto() is True


def test_cerrar_y_abrir_claude_de_microsoft_store(windows):
    assert procesos.cerrar_claude() is True
    assert procesos.claude_abierto() is False
    assert procesos.abrir_claude() is True
    assert windows.lanzados == [["explorer.exe", "shell:AppsFolder\\Claude_pzs8sxrjxfjjc!Claude"]]


def test_abrir_claude_clasico(windows, tmp_path):
    exe = tmp_path / "Local" / "AnthropicClaude" / "claude.exe"
    exe.parent.mkdir(parents=True)
    exe.write_text("")
    assert procesos.comando_abrir_claude() == [str(exe)]


def test_sin_claude_instalado_no_se_abre(windows):
    windows.app_tienda = ""
    assert procesos.abrir_claude() is False


def test_reiniciar_y_conectar_desde_el_panel(windows, monkeypatch):
    monkeypatch.setattr(panel.sys, "platform", "win32")
    r = panel.reiniciar_claude(conectar=True)
    assert r["ok"] and "Conectado" in r["mensaje"]
    assert registrar.esta_registrado(registrar.ruta_activa())
    assert windows.lanzados  # Claude se volvió a abrir


def test_reiniciar_fuera_de_windows():
    assert panel.reiniciar_claude(conectar=False)["ok"] is False


@pytest.fixture
def url():
    import threading

    servidor = panel.crear_servidor(0)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{servidor.server_address[1]}"
    servidor.shutdown()
    servidor.server_close()


def test_conectar_con_claude_abierto_avisa_para_ofrecer_el_reinicio(url, monkeypatch):
    monkeypatch.setenv("MCPAUTOCAD_CLAUDE_ABIERTO", "1")
    req = urllib.request.Request(url + "/api/registrar", data=b"{}", headers={"Content-Type": "application/json"})
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(req, timeout=5)
    assert e.value.code == 409
    assert json.loads(e.value.read())["claude_abierto"] is True


def test_estado_incluye_programas_abiertos(url):
    with urllib.request.urlopen(url + "/api/estado", timeout=5) as r:
        e = json.loads(r.read())
    assert {"abierto"} <= set(e["claude"]) and "autocad" in e and "puede_reiniciar" in e


def test_diagnostico_en_vivo_envia_cada_paso(url):
    from mcpautocad import configuracion

    configuracion.guardar({"motor": "ezdxf"})
    with urllib.request.urlopen(url + "/api/diagnostico/en-vivo", timeout=60) as r:
        assert r.headers["Content-Type"].startswith("text/event-stream")
        texto = r.read().decode()
    eventos = [b.split("\n") for b in texto.strip().split("\n\n")]
    nombres = [e[0].removeprefix("event: ") for e in eventos]
    assert nombres[-1] == "fin" and nombres.count("paso") >= 4
    fin = json.loads(eventos[-1][1].removeprefix("data: "))
    assert {"ok", "resumen", "informe"} <= set(fin)
