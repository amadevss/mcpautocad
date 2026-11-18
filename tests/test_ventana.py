"""Ventana propia del panel (modo aplicación de Edge/Chrome)."""

import subprocess
import sys
import threading
import time

from mcpautocad import panel, ventana


def test_comando_de_ventana_de_aplicacion(tmp_path, monkeypatch):
    navegador = tmp_path / "msedge.exe"
    navegador.write_text("")
    monkeypatch.setenv("MCPAUTOCAD_NAVEGADOR", str(navegador))
    assert ventana.buscar_navegador() == navegador
    args = ventana.comando(navegador, "http://localhost:8765/")
    assert args[1] == "--app=http://localhost:8765/"
    assert any(a.startswith("--user-data-dir=") and "ventana" in a for a in args)


def test_sin_navegador_usa_el_navegador_normal(monkeypatch, tmp_path):
    monkeypatch.setenv("MCPAUTOCAD_NAVEGADOR", str(tmp_path / "no-existe.exe"))
    abiertas = []
    monkeypatch.setattr(ventana.webbrowser, "open", abiertas.append)
    assert ventana.abrir("http://localhost:1/") is None
    assert abiertas == ["http://localhost:1/"]


def _proceso(segundos):
    return subprocess.Popen([sys.executable, "-c", f"import time; time.sleep({segundos})"])


def test_al_cerrar_la_ventana_se_cierra_el_panel():
    cerrado = []
    ventana.esperar_cierre(_proceso(0.5), lambda: cerrado.append(True), minimo=0.2)
    assert cerrado == [True]


def test_si_paso_la_pagina_a_otra_ventana_no_se_cierra():
    cerrado = []
    ventana.esperar_cierre(_proceso(0), lambda: cerrado.append(True), minimo=5)
    assert cerrado == []


def test_el_panel_se_cierra_si_nadie_lo_usa():
    servidor = panel.crear_servidor(0)
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    servidor.ultimo_uso = time.monotonic() - 100
    threading.Thread(target=panel._vigilar_inactividad, args=(servidor, 0.4), daemon=True).start()
    hilo.join(timeout=5)
    assert not hilo.is_alive()
    servidor.server_close()
