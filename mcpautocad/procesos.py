"""Claude Desktop y AutoCAD como programas: si están abiertos, y cerrar/abrir Claude.

Solo hace algo en Windows. En otros sistemas responde «no se sabe» (None) o
False, para que el panel lo muestre como «sin comprobar».
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

SIN_VENTANA = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _windows() -> bool:
    return sys.platform == "win32"


def proceso_abierto(nombre: str) -> bool | None:
    """¿Hay algún proceso con ese nombre de programa? None si no se puede saber."""
    if not _windows():
        return None
    try:
        salida = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {nombre}", "/NH"], capture_output=True,
                                text=True, timeout=10, creationflags=SIN_VENTANA)
        return nombre.lower() in salida.stdout.lower()
    except Exception:
        return None


def claude_abierto() -> bool | None:
    if os.environ.get("MCPAUTOCAD_CLAUDE_ABIERTO"):  # para pruebas
        return os.environ["MCPAUTOCAD_CLAUDE_ABIERTO"] == "1"
    return proceso_abierto("claude.exe")


def autocad_abierto() -> bool | None:
    return proceso_abierto("acad.exe")


def cerrar_claude(espera: float = 15) -> bool:
    """Cierra Claude Desktop del todo (también el icono de la bandeja). True si quedó cerrado.

    Se fuerza el cierre porque cerrar la ventana solo lo manda a la bandeja. Las
    conversaciones de Claude se guardan en la nube, no se pierden.
    """
    if not _windows():
        return False
    subprocess.run(["taskkill", "/IM", "claude.exe", "/T", "/F"], capture_output=True, timeout=20,
                   creationflags=SIN_VENTANA)
    limite = time.monotonic() + espera
    while time.monotonic() < limite:
        if not claude_abierto():
            time.sleep(1)  # que termine de soltar sus archivos
            return True
        time.sleep(0.5)
    return False


def _id_app_tienda() -> str:
    """Identificador de Claude de Microsoft Store para abrirlo (p. ej. «Claude_xxxx!Claude»)."""
    orden = ("Get-StartApps | Where-Object { $_.AppID -like 'Claude_*!*' -or $_.Name -eq 'Claude' } | "
             "Select-Object -First 1 -ExpandProperty AppID")
    try:
        salida = subprocess.run(["powershell", "-NoProfile", "-Command", orden], capture_output=True, text=True,
                                timeout=20, creationflags=SIN_VENTANA)
        return salida.stdout.strip().splitlines()[0].strip() if salida.stdout.strip() else ""
    except Exception:
        return ""


def comando_abrir_claude() -> list[str] | None:
    """Cómo abrir Claude Desktop en este equipo, o None si no se encuentra."""
    if not _windows():
        return None
    local = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    clasico = local / "AnthropicClaude" / "claude.exe"
    if clasico.exists():
        return [str(clasico)]
    app = _id_app_tienda()
    if app:
        return ["explorer.exe", f"shell:AppsFolder\\{app}"]
    return None


def abrir_claude() -> bool:
    comando = comando_abrir_claude()
    if not comando:
        return False
    # Independiente del panel: Claude sigue abierto aunque se cierre MCP AutoCAD.
    banderas = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    try:
        subprocess.Popen(comando, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         creationflags=banderas, close_fds=True)
        return True
    except OSError:
        return False
