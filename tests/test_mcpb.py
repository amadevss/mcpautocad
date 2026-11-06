"""Extensión .mcpb: el manifiesto y la lectura de su configuración."""

import asyncio
import json
import os
import re
import sys
from pathlib import Path

import pytest
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

from mcpautocad import configuracion

RAIZ = Path(__file__).resolve().parents[1]
MANIFIESTO = json.loads((RAIZ / "mcpb" / "manifest.json").read_text(encoding="utf-8"))


def sustituir(valores: dict) -> dict[str, str]:
    """Hace lo mismo que Claude Desktop: cambia ${user_config.x} por el valor elegido."""
    usuario = {k: v.get("default") for k, v in MANIFIESTO["user_config"].items()}
    usuario.update(valores)

    def texto(v):
        return ("true" if v else "false") if isinstance(v, bool) else str(v)

    return {
        nombre: re.sub(r"\$\{user_config\.(\w+)\}", lambda m: texto(usuario[m.group(1)]), valor)
        for nombre, valor in MANIFIESTO["server"]["mcp_config"]["env"].items()
    }


def test_cada_campo_del_formulario_llega_al_servidor():
    usados = set(re.findall(r"\$\{user_config\.(\w+)\}", json.dumps(MANIFIESTO["server"])))
    assert usados == set(MANIFIESTO["user_config"])
    env = MANIFIESTO["server"]["mcp_config"]["env"]
    assert env["MCPAUTOCAD_ORIGEN"] == configuracion.ORIGEN_MCPB
    for paquete in configuracion.PAQUETES:
        assert f"MCPAUTOCAD_{paquete.upper()}" in env


def test_ejecuta_el_programa_empaquetado():
    cfg = MANIFIESTO["server"]["mcp_config"]
    assert cfg["command"] == "${__dirname}/" + MANIFIESTO["server"]["entry_point"]
    assert cfg["args"] == ["servidor"]
    assert MANIFIESTO["icon"] == "icon.png"
    assert MANIFIESTO["compatibility"]["platforms"] == ["win32"]


def test_valores_por_defecto_iguales_que_el_panel():
    cfg = configuracion.desde_entorno(sustituir({}))
    assert cfg == {**configuracion.POR_DEFECTO, "motor": "com"}


@pytest.mark.parametrize("escrito,modo", [
    ("ligero", "ligero"), ("Completo", "completo"), ("búsqueda", "busqueda"), (" Busqueda ", "busqueda"),
    ("search", "busqueda"), ("lean", "ligero"), ("cualquier cosa", "ligero"), ("", "ligero"),
])
def test_modo_escrito_a_mano(escrito, modo):
    assert configuracion.desde_entorno(sustituir({"modo": escrito}))["modo"] == modo


def test_paquetes_y_3d():
    cfg = configuracion.desde_entorno(sustituir({"mecanica": False, "planta": False, "tres_d": True}))
    assert cfg["paquetes"] == ["arquitectura", "pid", "configuracion"]
    assert cfg["3d"] is True


def test_variables_sin_sustituir_usan_el_valor_por_defecto():
    env = MANIFIESTO["server"]["mcp_config"]["env"]  # tal cual, con ${user_config.x}
    assert configuracion.desde_entorno(env) == {**configuracion.POR_DEFECTO}


def test_la_extension_manda_sobre_config_json(monkeypatch):
    configuracion.guardar({"modo": "completo"})
    for nombre, valor in sustituir({"modo": "busqueda"}).items():
        monkeypatch.setenv(nombre, valor)
    assert configuracion.cargar_para_servidor()["modo"] == "busqueda"
    monkeypatch.delenv("MCPAUTOCAD_ORIGEN")
    assert configuracion.cargar_para_servidor()["modo"] == "completo"


@pytest.mark.parametrize("valores,esperadas", [
    ({}, 66),
    ({"modo": "busqueda"}, 3),
    ({"modo": "completo", "mecanica": False, "arquitectura": False, "pid": False,
      "planta": False, "configuracion": False}, 182),  # 184 menos las 2 apagadas por defecto
    ({"modo": "completo", "tres_d": True}, 246),
    ({"modo": "completo", "desactivadas": ""}, 243),  # el usuario borra el campo: todas
])
def test_servidor_con_la_config_de_la_extension(valores, esperadas):
    async def listar():
        env = {**os.environ, **sustituir(valores), "MCPAUTOCAD_MOTOR": "ezdxf", "LOG_LEVEL": "ERROR"}
        exe = os.environ.get("MCPAUTOCAD_EXE")  # en GitHub Actions: el .exe empaquetado
        comando, args = (exe, ["servidor"]) if exe else (sys.executable, ["-m", "mcpautocad", "servidor"])
        transporte = StdioTransport(command=comando, args=args, env=env)
        async with Client(transporte) as cliente:
            return await cliente.list_tools()

    assert len(asyncio.run(listar())) == esperadas
