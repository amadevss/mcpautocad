# -*- mode: python ; coding: utf-8 -*-
# Receta de PyInstaller para mcpautocad.exe. La usa construir.ps1.
#
# El servidor original (autocad-mcp-pro) instala módulos sueltos con nombres
# genéricos (server, config, backends, ...) y lee archivos junto a su código
# (templates/, engineering/recipes/data). Por eso se recogen a mano.
import sys
from PyInstaller.utils.hooks import collect_all, collect_submodules, copy_metadata

ORIGINAL_MODULOS = ["server", "config", "security", "version"]
ORIGINAL_PAQUETES = ["backends", "discovery", "engineering"]

datas, binaries, hiddenimports = [], [], list(ORIGINAL_MODULOS)
def _sin_cli(nombre):
    # mcp.cli necesita typer y no se usa: importarlo aborta la recogida.
    return nombre != "mcp.cli" and not nombre.startswith("mcp.cli.")

for paquete in ORIGINAL_PAQUETES + ["fastmcp", "mcp", "ezdxf"]:
    d, b, h = collect_all(paquete, filter_submodules=_sin_cli)
    datas += d; binaries += b; hiddenimports += h
hiddenimports += collect_submodules("mcpautocad")
if sys.platform == "win32":
    hiddenimports += ["win32com", "win32com.client", "pythoncom", "pywintypes"]

import importlib.util, os
_templates = os.path.join(os.path.dirname(importlib.util.find_spec("server").origin), "templates")
datas += [(_templates, "templates")]
datas += [("mcpautocad/catalogo.json", "mcpautocad"), ("mcpautocad/panel.html", "mcpautocad"),
          ("mcpautocad/icono.png", "mcpautocad")]
for dist in ["autocad-mcp-pro", "fastmcp", "mcp", "ezdxf", "pydantic", "matplotlib", "openpyxl", "pillow"]:
    try:
        datas += copy_metadata(dist)
    except Exception:
        pass

a = Analysis(
    ["lanzador.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["tkinter", "pytest", "IPython"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="mcpautocad",
    console=True,          # Claude Desktop habla con el servidor por stdin/stdout
    icon="instalador/icono.ico" if os.path.exists("instalador/icono.ico") else None,
)
coll = COLLECT(exe, a.binaries, a.datas, name="mcpautocad")
