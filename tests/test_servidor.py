"""Arranca el servidor de verdad (motor ezdxf, sin AutoCAD) y cuenta las herramientas.

Con MCPAUTOCAD_EXE=ruta\\mcpautocad.exe se prueba el programa empaquetado en vez
del código fuente (lo hace GitHub Actions después de construir).
"""

import asyncio
import os
import sys

import pytest
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

from mcpautocad import catalogo, configuracion

def transporte():
    exe = os.environ.get("MCPAUTOCAD_EXE")
    comando, args = (exe, ["servidor"]) if exe else (sys.executable, ["-m", "mcpautocad", "servidor"])
    return StdioTransport(command=comando, args=args, env={**os.environ, "LOG_LEVEL": "ERROR"})


TODAS = {"desactivadas": []}  # cifras del original tal cual, sin las apagadas por defecto

CASOS = [
    ({"modo": "completo", "paquetes": list(configuracion.PAQUETES), **TODAS}, 243),
    ({"modo": "completo", "paquetes": list(configuracion.PAQUETES), "3d": True, **TODAS}, 248),
    ({"modo": "completo", "paquetes": [], **TODAS}, 184),
    ({"modo": "completo", "paquetes": ["mecanica"], **TODAS}, 198),
    ({"modo": "completo"}, 241),  # por defecto: system_run_command y system_run_lisp apagadas
    ({"modo": "ligero", "paquetes": list(configuracion.PAQUETES)}, 66),
    ({"modo": "ligero", "paquetes": []}, 56),
    ({"modo": "busqueda", "paquetes": list(configuracion.PAQUETES)}, 3),
]


async def listar(cfg):
    configuracion.guardar({**cfg, "motor": "ezdxf"})
    async with Client(transporte()) as cliente:
        return [h.name for h in await cliente.list_tools()]


@pytest.mark.parametrize("cfg,esperadas", CASOS)
def test_servidor_lista_herramientas_segun_config(cfg, esperadas):
    nombres = asyncio.run(listar(cfg))
    assert len(nombres) == esperadas
    # El panel predice exactamente lo mismo.
    assert catalogo.estimar(cfg)["herramientas"] == esperadas
    if cfg["modo"] != "busqueda":
        assert sorted(nombres) == sorted(h["nombre"] for h in catalogo.visibles(cfg))
    if cfg["modo"] == "busqueda":
        assert set(nombres) == {"search_tools", "call_tool", "describe_tool"}


def test_dibuja_una_linea_y_guarda_dxf(tmp_path):
    destino = tmp_path / "prueba.dxf"

    async def dibujar():
        configuracion.guardar({"modo": "ligero", "motor": "ezdxf"})
        async with Client(transporte()) as cliente:
            # Con plantilla: comprueba que las plantillas del original van incluidas.
            await cliente.call_tool("drawing_new", {"template": "iso_a3_mech"})
            await cliente.call_tool("entity_create_line", {"x1": 0, "y1": 0, "x2": 100, "y2": 50})
            await cliente.call_tool("drawing_save_as", {"path": str(destino)})

    asyncio.run(dibujar())
    import ezdxf

    lineas = [e for e in ezdxf.readfile(destino).modelspace() if e.dxftype() == "LINE"]
    assert any(tuple(e.dxf.end)[:2] == (100, 50) for e in lineas)


def test_tokens_aproximados_del_panel():
    completo = catalogo.estimar({"modo": "completo", "paquetes": list(configuracion.PAQUETES)})["tokens"]
    ligero = catalogo.estimar({"modo": "ligero", "paquetes": list(configuracion.PAQUETES)})["tokens"]
    busqueda = catalogo.estimar({"modo": "busqueda"})["tokens"]
    assert 80_000 < completo < 120_000
    assert 20_000 < ligero < 35_000
    assert busqueda < 1_000
