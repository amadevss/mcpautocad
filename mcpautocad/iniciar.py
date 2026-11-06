"""Arranca el servidor MCP original por stdio con la configuración del usuario.

Claude Desktop ejecuta esto (``mcpautocad.exe servidor``). Nada debe escribirse
en stdout salvo el protocolo MCP: los mensajes van a stderr.
"""

from __future__ import annotations

import os
import sys

from . import configuracion


def preparar_entorno(cfg: dict | None = None) -> dict[str, str]:
    """Pone las variables de entorno según la configuración y las devuelve.

    La configuración del panel (o la del formulario de la extensión .mcpb)
    siempre manda, para que lo que ve el usuario sea lo que ve Claude.
    """
    cfg = configuracion.cargar_para_servidor() if cfg is None else cfg
    variables = configuracion.variables_entorno(cfg)
    os.environ.update(variables)
    return variables


def quitar_herramientas(mcp, nombres: list[str]) -> list[str]:
    """Quita del servidor las herramientas desactivadas una por una.

    Se borran del registro antes de arrancar, así no se anuncian ni se pueden
    llamar (tampoco desde el modo Búsqueda). Un nombre que no existe (por
    ejemplo, de otra versión del original) se ignora.
    """
    quitadas = []
    for nombre in nombres:
        try:
            mcp.local_provider.remove_tool(nombre)
            quitadas.append(nombre)
        except Exception:  # KeyError / NotFoundError según la versión de fastmcp
            print(f"MCP AutoCAD: la herramienta {nombre!r} no existe, se ignora.", file=sys.stderr)
    return quitadas


def main() -> None:
    cfg = configuracion.cargar_para_servidor()
    variables = preparar_entorno(cfg)
    # Sin banner ni búsqueda de actualizaciones de fastmcp en cada arranque.
    os.environ.setdefault("FASTMCP_SHOW_SERVER_BANNER", "false")
    os.environ.setdefault("FASTMCP_CHECK_FOR_UPDATES", "off")
    print("MCP AutoCAD: " + ", ".join(f"{k}={v}" for k, v in variables.items()), file=sys.stderr)
    # Se importa después de poner las variables: el original las lee al importarse.
    import server  # módulo de autocad-mcp-pro

    quitadas = quitar_herramientas(server.mcp, cfg["desactivadas"])
    if quitadas:
        print(f"MCP AutoCAD: {len(quitadas)} herramientas desactivadas a mano.", file=sys.stderr)
    server.mcp.run()


if __name__ == "__main__":
    main()
