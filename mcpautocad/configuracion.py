"""Lee y guarda la configuración del usuario y la traduce a variables de entorno.

La configuración vive en %APPDATA%\\mcpautocad\\config.json (en Linux/macOS,
~/.config/mcpautocad/config.json). La variable MCPAUTOCAD_CONFIG cambia la ruta
(la usan los tests).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

#: Modos del panel -> variables del servidor original.
MODOS = ("completo", "ligero", "busqueda")

#: Paquetes opcionales: nombre en el panel -> nombre en TOOL_PACKS.
#: "core" (Básico) siempre va activo y no aparece aquí.
PAQUETES = {
    "mecanica": "mech",
    "arquitectura": "arch",
    "pid": "pid",
    "planta": "plant",
    "configuracion": "settings",
}

#: Motores: "com" = AutoCAD real (Windows), "ezdxf" = sin AutoCAD, "auto" = el que haya.
MOTORES = ("com", "ezdxf", "auto")

#: Otras formas de escribir el modo (la extensión .mcpb lo pide como texto libre).
ALIAS_MODO = {
    "búsqueda": "busqueda", "buscar": "busqueda", "search": "busqueda",
    "lean": "ligero", "liviano": "ligero",
    "full": "completo", "todo": "completo", "todas": "completo",
}

#: Variables que rellena la extensión .mcpb desde su formulario (ver mcpb/manifest.json).
ORIGEN_MCPB = "mcpb"

POR_DEFECTO: dict = {
    "modo": "ligero",
    "paquetes": list(PAQUETES),
    "3d": False,
    "motor": "com",
}


def carpeta_config() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / "mcpautocad"
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "mcpautocad"


def ruta_config() -> Path:
    propia = os.environ.get("MCPAUTOCAD_CONFIG", "").strip()
    return Path(propia) if propia else carpeta_config() / "config.json"


def normalizar(datos: dict | None) -> dict:
    """Devuelve una configuración válida; lo desconocido o erróneo se cambia por el valor por defecto."""
    datos = datos if isinstance(datos, dict) else {}
    cfg = dict(POR_DEFECTO)

    modo = str(datos.get("modo", cfg["modo"])).lower().strip()
    modo = ALIAS_MODO.get(modo, modo)
    cfg["modo"] = modo if modo in MODOS else POR_DEFECTO["modo"]

    paquetes = datos.get("paquetes", cfg["paquetes"])
    if isinstance(paquetes, list):
        # Conserva el orden de PAQUETES y quita repetidos o desconocidos.
        cfg["paquetes"] = [p for p in PAQUETES if p in paquetes]

    cfg["3d"] = datos.get("3d", False) is True

    motor = str(datos.get("motor", cfg["motor"])).lower().strip()
    cfg["motor"] = motor if motor in MOTORES else POR_DEFECTO["motor"]
    return cfg


def cargar(ruta: Path | None = None) -> dict:
    ruta = ruta or ruta_config()
    try:
        return normalizar(json.loads(ruta.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return normalizar(None)


def guardar(cfg: dict, ruta: Path | None = None) -> dict:
    ruta = ruta or ruta_config()
    cfg = normalizar(cfg)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = ruta.with_suffix(".tmp")
    temporal.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporal, ruta)
    return cfg


def variables_entorno(cfg: dict) -> dict[str, str]:
    """Variables que entiende el servidor original (verificadas en su config.py v1.7.0)."""
    cfg = normalizar(cfg)
    packs = ["core"] + [PAQUETES[p] for p in cfg["paquetes"]]
    return {
        "AUTOCAD_MCP_BACKEND": cfg["motor"],
        "TOOL_PROFILE": "lean" if cfg["modo"] == "ligero" else "full",
        "DISCOVERY_MODE": "search" if cfg["modo"] == "busqueda" else "off",
        "TOOL_PACKS": ",".join(packs),
        "ENABLE_3D": "true" if cfg["3d"] else "false",
        "DANGEROUS_COMMANDS_ENABLED": "false",
    }


def _si(valor: str | None, defecto: bool) -> bool:
    if valor is None or not valor.strip() or valor.strip().startswith("${"):
        return defecto  # sin valor (o sin sustituir): el valor por defecto
    return valor.strip().lower() in ("true", "1", "si", "sí", "yes")


def desde_entorno(entorno: dict[str, str] | None = None) -> dict:
    """Configuración que llega en variables MCPAUTOCAD_* (la pone la extensión .mcpb).

    MCPAUTOCAD_MODO, MCPAUTOCAD_MECANICA, MCPAUTOCAD_ARQUITECTURA, MCPAUTOCAD_PID,
    MCPAUTOCAD_PLANTA, MCPAUTOCAD_CONFIGURACION, MCPAUTOCAD_3D y MCPAUTOCAD_MOTOR.
    """
    entorno = os.environ if entorno is None else entorno
    modo = entorno.get("MCPAUTOCAD_MODO", "")
    return normalizar({
        "modo": modo if modo.strip() and not modo.startswith("${") else POR_DEFECTO["modo"],
        "paquetes": [p for p in PAQUETES if _si(entorno.get(f"MCPAUTOCAD_{p.upper()}"), True)],
        "3d": _si(entorno.get("MCPAUTOCAD_3D"), False),
        "motor": entorno.get("MCPAUTOCAD_MOTOR") or POR_DEFECTO["motor"],
    })


def cargar_para_servidor() -> dict:
    """La que usa el servidor: la de la extensión .mcpb si viene de ahí; si no, config.json."""
    if os.environ.get("MCPAUTOCAD_ORIGEN", "").strip().lower() == ORIGEN_MCPB:
        return desde_entorno()
    return cargar()
