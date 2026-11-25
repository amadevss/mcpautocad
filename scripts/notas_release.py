"""Notas del Release: instrucciones de descarga + «Novedades» de esa versión sacadas de CHANGELOG.md.

Uso:  python scripts/notas_release.py 0.2.0 notas.md   (sin archivo: por pantalla)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
REPOSITORIO = "https://github.com/amadevss/mcpautocad/blob/main/"


def novedades(version: str, changelog: str) -> str:
    """El apartado «## [version]» del CHANGELOG, sin su título; vacío si no está."""
    partes = re.split(r"^## ", changelog, flags=re.M)
    for parte in partes:
        if parte.startswith(f"[{version}]"):
            cuerpo = parte.split("\n", 1)[1] if "\n" in parte else ""
            cuerpo = re.sub(r"^\[[^\]]+\]: .*$", "", cuerpo, flags=re.M).strip()
            # En la página del Release los enlaces relativos (docs/GUIA.md) no funcionan.
            return re.sub(r"\]\((?!https?://|#)([^)]+)\)", lambda m: f"]({REPOSITORIO}{m.group(1)})", cuerpo)
    return ""


def notas(version: str) -> str:
    base = (RAIZ / "docs" / "NOTAS_RELEASE.md").read_text(encoding="utf-8").strip()
    cambios = novedades(version, (RAIZ / "CHANGELOG.md").read_text(encoding="utf-8"))
    if cambios:
        return f"## ✨ Novedades de la {version}\n\n{cambios}\n\n{base}\n"
    return base + "\n"


if __name__ == "__main__":
    texto = notas(sys.argv[1])
    if len(sys.argv) > 2:  # archivo en UTF-8: la redirección de PowerShell podría estropear los acentos
        Path(sys.argv[2]).write_text(texto, encoding="utf-8")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(texto, end="")
