"""Agrega o quita este MCP en la configuración de Claude Desktop sin tocar otros servidores.

Dónde guarda Claude Desktop su configuración en Windows (comprobado en un equipo
real con Claude Desktop 5.11492 de Microsoft Store, ver docs/PLAN.md):

1. Datos «reubicados»: %LOCALAPPDATA%\\Claude-Data\\<familia del paquete>\\. En
   main.log aparece ``user_data_location: 'relocated_local'`` y en
   %APPDATA%\\Claude queda un marcador ``.user-data-left.*``.
2. Microsoft Store sin reubicar: %LOCALAPPDATA%\\Packages\\Claude_*\\LocalCache\\
   Roaming\\Claude\\ (la virtualización de MSIX).
3. Instalador clásico: %APPDATA%\\Claude\\.

Los registros están en %LOCALAPPDATA%\\Claude\\logs\\ (o junto a la configuración en
instalaciones clásicas). Claude reescribe su configuración mientras está abierto,
así que solo se escribe con Claude cerrado.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

NOMBRE = "autocad"
ARCHIVO = "claude_desktop_config.json"
COPIA = ARCHIVO + ".bak-mcpautocad"

#: Nombre del programa de consola: el que arranca Claude Desktop (habla por stdin/stdout).
PROGRAMA_CONSOLA = "mcpautocad.exe" if sys.platform == "win32" else "mcpautocad"


class ConfigInvalida(Exception):
    """El archivo de Claude Desktop existe pero no es JSON válido: no lo tocamos."""


class ClaudeAbierto(Exception):
    """Claude Desktop está abierto: reescribiría la configuración y se perdería el cambio."""

    def __init__(self):
        super().__init__("Claude Desktop está abierto. Ciérralo por completo (clic derecho en su icono junto al "
                         "reloj → Salir) y vuelve a intentarlo: si no, Claude borra el cambio al guardar su "
                         "configuración.")


# ── dónde está la configuración ─────────────────────────────────────────────


def _carpetas_windows() -> tuple[Path, Path]:
    appdata = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    local = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    return appdata, local


def ubicaciones_windows(appdata: Path, local: Path) -> dict:
    """Las configuraciones posibles de Claude Desktop en Windows y cuál usa de verdad.

    Devuelve ``{"activa": Path, "candidatas": [Path, ...], "tipo": str, "logs": [Path, ...]}``.
    No inventa nombres de paquete: los lee de las carpetas que existen.
    """
    paquetes = sorted(p for p in (local / "Packages").glob("Claude_*") if p.is_dir())
    familias = {p.name.lower() for p in paquetes}
    datos = local / "Claude-Data"
    reubicadas = sorted((d for d in datos.iterdir() if d.is_dir()), key=lambda d: d.name.lower() not in familias) \
        if datos.is_dir() else []
    tienda = [p / "LocalCache" / "Roaming" / "Claude" / ARCHIVO for p in paquetes]
    clasica = appdata / "Claude" / ARCHIVO

    if reubicadas:
        activa, tipo = reubicadas[0] / ARCHIVO, "reubicada"
    elif tienda:
        activa, tipo = tienda[0], "tienda"
    else:
        activa, tipo = clasica, "clasica"

    candidatas = [activa]
    for ruta in [d / ARCHIVO for d in reubicadas] + tienda + [clasica]:
        if ruta not in candidatas:
            candidatas.append(ruta)

    logs = [local / "Claude" / "logs", appdata / "Claude" / "logs", activa.parent / "logs"]
    logs += [r.parent / "logs" for r in tienda]
    return {"activa": activa, "candidatas": candidatas, "tipo": tipo, "logs": list(dict.fromkeys(logs))}


def ubicaciones() -> dict:
    """Como ``ubicaciones_windows`` pero para el sistema actual.

    MCPAUTOCAD_CLAUDE_CONFIG fuerza una ruta (la usan los tests).
    """
    propia = os.environ.get("MCPAUTOCAD_CLAUDE_CONFIG", "").strip()
    if propia:
        ruta = Path(propia)
        return {"activa": ruta, "candidatas": [ruta], "tipo": "forzada", "logs": [ruta.parent / "logs"]}
    if sys.platform == "win32":
        return ubicaciones_windows(*_carpetas_windows())
    if sys.platform == "darwin":
        ruta = Path.home() / "Library" / "Application Support" / "Claude" / ARCHIVO
        return {"activa": ruta, "candidatas": [ruta], "tipo": "macos",
                "logs": [Path.home() / "Library" / "Logs" / "Claude"]}
    ruta = Path.home() / ".config" / "Claude" / ARCHIVO
    return {"activa": ruta, "candidatas": [ruta], "tipo": "linux", "logs": [ruta.parent / "logs"]}


def rutas_claude() -> list[Path]:
    """Todas las configuraciones posibles; la primera es la que usa Claude."""
    return ubicaciones()["candidatas"]


def ruta_activa() -> Path:
    return ubicaciones()["activa"]


def es_tienda(ruta: Path) -> bool:
    """¿Es la configuración virtualizada de Claude de Microsoft Store (MSIX)?"""
    return any(p.startswith("Claude_") for p in ruta.parts) and "Packages" in ruta.parts


# ── Claude Desktop en marcha y políticas ─────────────────────────────────────


def claude_abierto() -> bool:
    """¿Está Claude Desktop abierto? (solo Windows; en otros sistemas, no se comprueba)."""
    if os.environ.get("MCPAUTOCAD_CLAUDE_ABIERTO"):  # para pruebas
        return os.environ["MCPAUTOCAD_CLAUDE_ABIERTO"] == "1"
    if sys.platform != "win32":
        return False
    try:
        salida = subprocess.run(["tasklist", "/FI", "IMAGENAME eq claude.exe", "/NH"], capture_output=True,
                                text=True, timeout=10, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return "claude.exe" in salida.stdout.lower()
    except Exception:
        return False


def politicas() -> list[str]:
    """Claves de políticas de empresa de Claude en el registro de Windows (pueden bloquear servidores locales)."""
    if sys.platform != "win32":
        return []
    import winreg

    encontradas = []
    for raiz, nombre in ((winreg.HKEY_LOCAL_MACHINE, "HKLM"), (winreg.HKEY_CURRENT_USER, "HKCU")):
        for clave in (r"SOFTWARE\Policies\Claude", r"SOFTWARE\Policies\Anthropic"):
            try:
                winreg.CloseKey(winreg.OpenKey(raiz, clave))
                encontradas.append(f"{nombre}\\{clave}")
            except OSError:
                pass
    return encontradas


# ── leer y escribir ──────────────────────────────────────────────────────────


def comando() -> dict:
    """Cómo debe arrancarnos Claude Desktop.

    Siempre el programa de consola, también cuando quien registra es la ventana
    del panel («MCP AutoCAD.exe», sin consola, que no sirve para stdio).
    """
    if getattr(sys, "frozen", False):  # .exe de PyInstaller
        consola = Path(sys.executable).with_name(PROGRAMA_CONSOLA)
        return {"command": str(consola if consola.exists() else Path(sys.executable)), "args": ["servidor"]}
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
    """Escritura atómica en UTF-8 sin BOM, con copia propia del archivo anterior."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    if ruta.exists():
        shutil.copy2(ruta, ruta.with_name(COPIA))
    temporal = ruta.with_name(ruta.name + ".tmp-mcpautocad")
    temporal.write_text(json.dumps(datos, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporal, ruta)


def agregar(ruta: Path) -> None:
    """Añade o actualiza solo ``mcpServers.autocad``; el resto del archivo queda igual."""
    datos = _leer(ruta)  # se lee justo antes de escribir
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
    """La configuración que usa Claude y, por si acaso, las otras candidatas que ya existen."""
    u = ubicaciones()
    return [u["activa"]] + [r for r in u["candidatas"][1:] if r.exists()]


def registrar_en_todas(comprobar_claude: bool = True) -> list[Path]:
    if comprobar_claude and claude_abierto():
        raise ClaudeAbierto()
    destinos = destinos_para_agregar()
    for ruta in destinos:
        agregar(ruta)
    return destinos


def quitar_de_todas(comprobar_claude: bool = True) -> list[Path]:
    if comprobar_claude and claude_abierto():
        raise ClaudeAbierto()
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
            print("Abre Claude Desktop para usar MCP AutoCAD.")
    except (ConfigInvalida, ClaudeAbierto) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2 if isinstance(error, ClaudeAbierto) else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
