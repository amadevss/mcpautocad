"""Punto de entrada: ``mcpautocad.exe [panel|servidor|registrar|quitar]``.

Sin argumentos (doble clic) abre el panel.
"""

from __future__ import annotations

import sys

AYUDA = """Uso: mcpautocad [orden]

  panel       Abre el panel de configuración en el navegador (por defecto).
  servidor    Arranca el servidor MCP por stdio (lo usa Claude Desktop).
  registrar   Agrega este MCP a Claude Desktop.
  quitar      Quita este MCP de Claude Desktop.
"""


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    orden = argv[0].lower().lstrip("-") if argv else "panel"
    if orden == "servidor":
        from . import iniciar

        iniciar.main()
        return 0
    if orden == "panel":
        from . import panel

        return panel.main(argv[1:])
    if orden in ("registrar", "quitar"):
        from . import registrar

        return registrar.main([orden])
    print(AYUDA)
    return 0 if orden in ("ayuda", "help", "h") else 2


if __name__ == "__main__":
    raise SystemExit(main())
