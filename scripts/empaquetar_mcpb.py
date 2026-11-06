"""Crea la extensión de Claude Desktop (.mcpb) a partir del programa ya construido.

Uso:  python scripts/empaquetar_mcpb.py --version 0.1.0 [--servidor dist/mcpautocad] [--salida salida]

Junta mcpb/manifest.json (con la versión puesta), el icono, la licencia y la
carpeta de PyInstaller en salida/mcpb/, y la empaqueta con la herramienta
oficial @anthropic-ai/mcpb (necesita Node.js / npx).
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
MCPB_CLI = "@anthropic-ai/mcpb@2.1.2"


def preparar(version: str, servidor: Path, carpeta: Path) -> Path:
    if carpeta.exists():
        shutil.rmtree(carpeta)
    carpeta.mkdir(parents=True)
    manifiesto = json.loads((RAIZ / "mcpb" / "manifest.json").read_text(encoding="utf-8"))
    manifiesto["version"] = version
    (carpeta / "manifest.json").write_text(json.dumps(manifiesto, indent=2, ensure_ascii=False) + "\n",
                                           encoding="utf-8")
    shutil.copy2(RAIZ / "mcpb" / "icon.png", carpeta / "icon.png")
    shutil.copy2(RAIZ / "LICENSE", carpeta / "LICENSE")
    shutil.copytree(servidor, carpeta / "server")
    return carpeta


def npx() -> str:
    comando = shutil.which("npx") or shutil.which("npx.cmd")
    if not comando:
        raise SystemExit("No encuentro npx: instala Node.js para empaquetar la extensión .mcpb.")
    return comando


def main(argv: list[str] | None = None) -> int:
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument("--version", required=True)
    args.add_argument("--servidor", default=str(RAIZ / "dist" / "mcpautocad"))
    args.add_argument("--salida", default=str(RAIZ / "salida"))
    opciones = args.parse_args(argv)

    salida = Path(opciones.salida)
    carpeta = preparar(opciones.version, Path(opciones.servidor), salida / "mcpb")
    destino = salida / f"MCP-AutoCAD-{opciones.version}.mcpb"
    subprocess.run([npx(), "-y", MCPB_CLI, "validate", str(carpeta / "manifest.json")], check=True)
    subprocess.run([npx(), "-y", MCPB_CLI, "pack", str(carpeta), str(destino)], check=True)
    shutil.rmtree(carpeta)
    print(f"Extensión creada: {destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
