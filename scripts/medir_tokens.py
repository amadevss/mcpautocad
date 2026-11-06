"""Mide el catálogo real del servidor original y genera mcpautocad/catalogo.json.

Arranca el servidor (motor ezdxf, no necesita AutoCAD) con distintas
combinaciones de TOOL_PROFILE / TOOL_PACKS / ENABLE_3D / DISCOVERY_MODE y anota,
por cada herramienta, a qué paquete pertenece, si está en el modo Ligero, si es
de 3D y cuántos tokens cuesta su definición (caracteres JSON / 4, aproximado).

Uso:  python scripts/medir_tokens.py
Hay que volver a ejecutarlo al cambiar la versión de autocad-mcp-pro.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from pathlib import Path

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from mcpautocad import VERSION_ORIGINAL  # noqa: E402
from mcpautocad.configuracion import PAQUETES  # noqa: E402

CARACTERES_POR_TOKEN = 4


DESCRIPCIONES: dict[str, str] = {}


def _resumen(texto: str | None) -> str:
    """Primera frase de la descripción (en inglés, como la escribe el original)."""
    texto = " ".join((texto or "").split())
    # Corta en el primer ". " o "; " que no sea parte de "e.g." / "i.e." / "etc.".
    fin = re.search(r"(?<!\be\.g)(?<!\bi\.e)(?<!\betc)[.;] ", texto)
    if fin:
        texto = texto[:fin.start()] + "."
    return texto if len(texto) <= 160 else texto[:157].rstrip() + "..."


async def _listar(env: dict[str, str]) -> dict[str, int]:
    entorno = {**os.environ, "AUTOCAD_MCP_BACKEND": "ezdxf", "LOG_LEVEL": "ERROR",
               "TOOL_PROFILE": "full", "TOOL_PACKS": "all", "ENABLE_3D": "false",
               "DISCOVERY_MODE": "off", **env}
    transporte = StdioTransport(command=sys.executable, args=["-m", "server"], env=entorno)
    async with Client(transporte) as cliente:
        herramientas = await cliente.list_tools()
    for h in herramientas:
        DESCRIPCIONES.setdefault(h.name, _resumen(h.description))
    return {
        h.name: len(json.dumps(h.model_dump(mode="json", exclude_none=True), ensure_ascii=False))
        for h in herramientas
    }


def listar(**env: str) -> dict[str, int]:
    return asyncio.run(_listar({k.upper(): v for k, v in env.items()}))


def main() -> None:
    todas = listar(enable_3d="true")
    sin_3d = listar()
    nucleo = listar(tool_packs="core")
    ligero = listar(tool_profile="lean", enable_3d="true")
    busqueda = listar(discovery_mode="search")

    paquete_de: dict[str, str] = {nombre: "basico" for nombre in nucleo}
    for nombre_panel, pack in PAQUETES.items():
        for nombre in set(listar(tool_packs=f"core,{pack}")) - set(nucleo):
            paquete_de[nombre] = nombre_panel
    solo_3d = set(todas) - set(sin_3d)
    for nombre in solo_3d:
        paquete_de.setdefault(nombre, "basico")

    sin_clasificar = set(todas) - set(paquete_de)
    if sin_clasificar:
        raise SystemExit(f"Herramientas sin paquete: {sorted(sin_clasificar)}")

    catalogo = {
        "version_original": VERSION_ORIGINAL,
        "caracteres_por_token": CARACTERES_POR_TOKEN,
        "busqueda": {"herramientas": len(busqueda),
                     "tokens": sum(busqueda.values()) // CARACTERES_POR_TOKEN},
        "herramientas": [
            {
                "nombre": nombre,
                "paquete": paquete_de[nombre],
                "ligero": nombre in ligero,
                "3d": nombre in solo_3d,
                "tokens": round(caracteres / CARACTERES_POR_TOKEN),
                "descripcion": DESCRIPCIONES.get(nombre, ""),
            }
            for nombre, caracteres in sorted(todas.items())
        ],
    }
    destino = RAIZ / "mcpautocad" / "catalogo.json"
    destino.write_text(json.dumps(catalogo, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    total = sum(h["tokens"] for h in catalogo["herramientas"])
    print(f"{len(todas)} herramientas, ~{total} tokens en total -> {destino}")


if __name__ == "__main__":
    main()
