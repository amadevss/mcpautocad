"""Estimación de herramientas y tokens según la configuración.

Los datos salen de catalogo.json, medido con scripts/medir_tokens.py sobre el
servidor real. Los tokens son aproximados (caracteres / 4).
"""

from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources

from . import configuracion


@lru_cache(maxsize=1)
def cargar() -> dict:
    return json.loads(resources.files(__package__).joinpath("catalogo.json").read_text(encoding="utf-8"))


def visibles(cfg: dict) -> list[dict]:
    """Herramientas que el servidor anunciará (en modo Búsqueda: las que Claude puede encontrar)."""
    cfg = configuracion.normalizar(cfg)
    paquetes = {"basico", *cfg["paquetes"]}
    return [
        h for h in cargar()["herramientas"]
        if h["paquete"] in paquetes
        and (cfg["3d"] or not h["3d"])
        and (cfg["modo"] != "ligero" or h["ligero"])
    ]


def estimar(cfg: dict) -> dict:
    """Herramientas anunciadas, tokens aproximados y herramientas por paquete.

    ``disponibles`` son las que Claude puede usar: en modo Búsqueda solo ve 3,
    pero a través de ellas llega a todas las disponibles.
    """
    cfg = configuracion.normalizar(cfg)
    lista = visibles(cfg)
    # Cuántas aportaría cada paquete en este modo, esté activo o no.
    todos = visibles({**cfg, "paquetes": list(configuracion.PAQUETES), "3d": True})
    por_paquete = {p: 0 for p in ("basico", *configuracion.PAQUETES, "3d")}
    for h in todos:
        por_paquete["3d" if h["3d"] else h["paquete"]] += 1
    if cfg["modo"] == "busqueda":
        b = cargar()["busqueda"]
        anunciadas, tokens = b["herramientas"], b["tokens"]
    else:
        anunciadas, tokens = len(lista), sum(h["tokens"] for h in lista)
    return {
        "herramientas": anunciadas,
        "tokens": tokens,
        "disponibles": len(lista),
        "por_paquete": por_paquete,
    }
