"""Botón «Diagnóstico»: cada causa por la que Claude no ve MCP AutoCAD da un mensaje claro."""

import json
import sys
from pathlib import Path

from mcpautocad import configuracion, diagnostico, registrar


def claude():
    return registrar.rutas_claude()[0]


def estados(r):
    return {p["titulo"]: p["estado"] for p in r["pasos"]}


def test_sin_registrar():
    claude().parent.mkdir(parents=True)
    r = diagnostico.diagnosticar(probar_servidor=False)
    assert not r["ok"]
    assert "Conectar con Claude Desktop" in r["resumen"]


def test_registrado_pero_claude_nunca_lo_arranco():
    registrar.agregar(claude())
    r = diagnostico.diagnosticar(probar_servidor=False)
    assert estados(r)["MCP AutoCAD registrado en Claude"] == "ok"
    assert estados(r)["Claude intentó arrancar MCP AutoCAD"] == "error"
    assert "Salir" in r["resumen"]  # reiniciar Claude desde la bandeja


def test_programa_registrado_ya_no_existe():
    claude().parent.mkdir(parents=True)
    claude().write_text(json.dumps({"mcpServers": {"autocad": {"command": "C:/no/existe.exe", "args": []}}}))
    r = diagnostico.diagnosticar(probar_servidor=False)
    paso = next(p for p in r["pasos"] if p["titulo"] == "MCP AutoCAD registrado en Claude")
    assert paso["estado"] == "error" and "no existe" in paso["detalle"]


def test_json_roto():
    claude().parent.mkdir(parents=True)
    claude().write_text("{roto")
    r = diagnostico.diagnosticar(probar_servidor=False)
    assert "no es JSON válido" in r["informe"]


def test_error_en_el_registro_de_claude():
    registrar.agregar(claude())
    logs = claude().parent / "logs"
    logs.mkdir()
    (logs / diagnostico.LOG).write_text(
        "2026-11-18 [autocad] [info] Initializing server...\n"
        '2026-11-18 [autocad] [info] {"description": "Raises an error if the layer is missing"}\n'
        "2026-11-18 [autocad] [error] spawn C:\\\\x\\\\mcpautocad.exe ENOENT\n")
    r = diagnostico.diagnosticar(probar_servidor=False)
    paso = next(p for p in r["pasos"] if p["titulo"] == "Claude intentó arrancar MCP AutoCAD")
    assert paso["estado"] == "error" and "ENOENT" in paso["detalle"]


def test_todo_bien_con_servidor_real():
    configuracion.guardar({"motor": "ezdxf"})
    registrar.agregar(claude())
    logs = claude().parent / "logs"
    logs.mkdir()
    (logs / diagnostico.LOG).write_text(
        '2026-11-18 [autocad] [info] Message from client: {"method":"initialize"}\n'
        '2026-11-18 [autocad] [info] {"tools":[{"description":"... returns an error when ..."}]}\n')
    r = diagnostico.diagnosticar()
    assert r["ok"], r["informe"]
    assert estados(r)["El servidor responde"] == "ok"
    assert r["informe"].startswith("Diagnóstico de MCP AutoCAD")


def test_ruta_de_microsoft_store():
    assert registrar.es_tienda(Path("C:/Users/a/AppData/Local/Packages/Claude_pzs8sxrjxfjjc/LocalCache/Roaming/"
                                    "Claude/claude_desktop_config.json"))
    assert not registrar.es_tienda(Path("C:/Users/a/AppData/Roaming/Claude/claude_desktop_config.json"))


def test_claude_siempre_recibe_el_programa_de_consola(tmp_path, monkeypatch):
    consola = tmp_path / registrar.PROGRAMA_CONSOLA
    consola.write_text("")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "MCP AutoCAD.exe"))
    assert registrar.comando() == {"command": str(consola), "args": ["servidor"]}
