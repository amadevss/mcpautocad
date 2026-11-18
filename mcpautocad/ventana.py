"""Abre el panel en una ventana propia, sin barra de direcciones ni pestañas.

Usa el modo «aplicación» de Microsoft Edge, que viene con Windows 10 y 11 (o
de Chrome si lo hay). Con un perfil propio, la ventana es un proceso aparte:
cuando el usuario la cierra, el panel también se cierra. Si no hay Edge ni
Chrome, se usa el navegador normal.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

from . import configuracion

ANCHO, ALTO = 1040, 900


def candidatos() -> list[Path]:
    """Dónde suele estar un navegador que sabe abrir ventanas de aplicación."""
    propio = os.environ.get("MCPAUTOCAD_NAVEGADOR", "").strip()  # para pruebas
    if propio:
        return [Path(propio)]
    if sys.platform == "win32":
        bases = [os.environ.get(v) for v in ("ProgramFiles(x86)", "ProgramFiles", "LOCALAPPDATA")]
        relativos = [r"Microsoft\Edge\Application\msedge.exe", r"Google\Chrome\Application\chrome.exe"]
        return [Path(b) / r for r in relativos for b in bases if b]
    nombres = ["microsoft-edge", "google-chrome", "chromium", "chromium-browser"]
    return [Path(p) for p in (shutil.which(n) for n in nombres) if p]


def buscar_navegador() -> Path | None:
    return next((p for p in candidatos() if p.exists()), None)


def perfil() -> Path:
    """Perfil propio del navegador para la ventana (no toca el del usuario)."""
    return configuracion.carpeta_config() / "ventana"


def comando(navegador: Path, url: str) -> list[str]:
    return [str(navegador), f"--app={url}", f"--user-data-dir={perfil()}", f"--window-size={ANCHO},{ALTO}",
            "--no-first-run", "--no-default-browser-check", "--disable-sync",
            # Sin la oferta de traducir la página (el panel ya está en español).
            "--lang=es-ES", "--disable-features=Translate,msTranslate"]


def abrir(url: str) -> subprocess.Popen | None:
    """Abre la ventana. Devuelve el proceso, o None si se usó el navegador normal."""
    navegador = buscar_navegador()
    if navegador is not None:
        try:
            perfil().mkdir(parents=True, exist_ok=True)
            return subprocess.Popen(comando(navegador, url), stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
        except OSError:
            pass
    webbrowser.open(url)
    return None


def esperar_cierre(proceso: subprocess.Popen, al_cerrar, minimo: float = 4.0) -> None:
    """Llama a ``al_cerrar`` cuando el usuario cierra la ventana.

    Si el proceso termina enseguida (menos de ``minimo`` segundos), es que otra
    ventana del mismo perfil ya estaba abierta y se le pasó la página: entonces
    no se cierra nada.
    """
    inicio = time.monotonic()
    proceso.wait()
    if time.monotonic() - inicio >= minimo:
        al_cerrar()
