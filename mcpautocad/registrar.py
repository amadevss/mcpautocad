"""Agrega o quita este MCP en la configuración de Claude Desktop sin tocar otros servidores."""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

NOMBRE = "autocad"


class ConfigInvalida(Exception):
    """El archivo de Claude Desktop existe pero no es JSON válido: no lo tocamos."""


def rutas_claude() -> list[Path]:
    """Archivos de configuración de Claude Desktop en este equipo.

    MCPAUTOCAD_CLAUDE_CONFIG fuerza una ruta (la usan los tests). En Windows se
    incluye también la ruta de la versión de Microsoft Store, si existe.
    """
    propia = os.environ.get("MCPAUTOCAD_CLAUDE_CONFIG", "").strip()
    if propia:
        return [Path(propia)]
    if sys.platform == "win32":
        appdata = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
        rutas = [appdata / "Claude" / "claude_desktop_config.json"]
        local = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
        for paquete in sorted((local / "Packages").glob("Claude_*")):
            rutas.append(paquete / "LocalCache" / "Roaming" / "Claude" / "claude_desktop_config.json")
        return rutas
    if sys.platform == "darwin":
        return [Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"]
    return [Path.home() / ".config" / "Claude" / "claude_desktop_config.json"]


def comando() -> dict:
    """Cómo debe arrancarnos Claude Desktop."""
    if getattr(sys, "frozen", False):  # .exe de PyInstaller
        return {"command": sys.executable, "args": ["servidor"]}
    return {"command": sys.executable, "args": ["-m", "mcpautocad", "servidor"]}


def _leer(ruta: Path) -> dict:
    if not ruta.exists():
        return {}
    texto = ruta.read_text(encoding="utf-8-sig").strip()
    if not texto:
        return {}
    try:
        datos = json.loads(texto)
    except ValueError as error:
        raise ConfigInvalida(f"{ruta} no es JSON válido ({error}). Corrígelo o bórralo y vuelve a intentar.")
    if not isinstance(datos, dict):
        raise ConfigInvalida(f"{ruta} no contiene un objeto JSON.")
    return datos


def _escribir(ruta: Path, datos: dict) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    if ruta.exists():
        shutil.copy2(ruta, ruta.with_name(ruta.name + ".bak"))
    temporal = ruta.with_name(ruta.name + ".tmp")
    temporal.write_text(json.dumps(datos, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporal, ruta)


def agregar(ruta: Path) -> None:
    datos = _leer(ruta)
    servidores = datos.get("mcpServers")
    if not isinstance(servidores, dict):
        servidores = {}
    servidores[NOMBRE] = comando()
    datos["mcpServers"] = servidores
    _escribir(ruta, datos)


def quitar(ruta: Path) -> bool:
    """Quita nuestra entrada. Devuelve True si había algo que quitar."""
    datos = _leer(ruta)
    servidores = datos.get("mcpServers")
    if not isinstance(servidores, dict) or NOMBRE not in servidores:
        return False
    del servidores[NOMBRE]
    _escribir(ruta, datos)
    return True


def esta_registrado(ruta: Path) -> bool:
    try:
        servidores = _leer(ruta).get("mcpServers")
    except ConfigInvalida:
        return False
    return isinstance(servidores, dict) and NOMBRE in servidores


def destinos_para_agregar() -> list[Path]:
    """Dónde registrar: las rutas cuya carpeta de Claude ya existe; si ninguna, la primera."""
    rutas = rutas_claude()
    existentes = [r for r in rutas if r.parent.exists()]
    return existentes or rutas[:1]


def registrar_en_todas() -> list[Path]:
    destinos = destinos_para_agregar()
    for ruta in destinos:
        agregar(ruta)
    return destinos


def quitar_de_todas() -> list[Path]:
    return [r for r in rutas_claude() if r.exists() and quitar(r)]


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    try:
        if argv and argv[0] in ("quitar", "--quitar"):
            quitadas = quitar_de_todas()
            print("Quitado de: " + ", ".join(map(str, quitadas)) if quitadas else "No estaba registrado.")
        else:
            for ruta in registrar_en_todas():
                print(f"Registrado en: {ruta}")
            print("Reinicia Claude Desktop para aplicar los cambios.")
    except ConfigInvalida as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
