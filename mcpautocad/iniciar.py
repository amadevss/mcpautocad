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


def main() -> None:
    variables = preparar_entorno()
    print("MCP AutoCAD: " + ", ".join(f"{k}={v}" for k, v in variables.items()), file=sys.stderr)
    # Se importa después de poner las variables: el original las lee al importarse.
    import server  # módulo de autocad-mcp-pro

    server.mcp.run()


if __name__ == "__main__":
    main()
