"""Diagnóstico: por qué Claude Desktop no ve (o no puede usar) MCP AutoCAD.

Revisa, en orden: dónde guarda Claude Desktop su configuración, si MCP AutoCAD
está registrado ahí y apunta a un programa que existe, si Claude intentó
arrancarlo (leyendo sus registros) y si el servidor responde. Cada comprobación
dice en español qué pasa y qué hacer. Lo usa el botón «Diagnóstico» del panel
y la orden ``mcpautocad diagnostico``.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

from . import __version__, VERSION_ORIGINAL, probar, registrar

OK, AVISO, ERROR = "ok", "aviso", "error"
LOG = "mcp-server-autocad.log"
# Fallos reales en el registro de Claude. No vale buscar "error" a secas: el registro
# incluye las descripciones de las herramientas, que lo mencionan a menudo.
_ERRORES = re.compile(r"\[error\]|Traceback|Server disconnected|transport closed unexpectedly|ENOENT|"
                      r"exited with code [1-9]|failed to start", re.IGNORECASE)


def _paso(titulo: str, estado: str, detalle: str, solucion: str = "") -> dict:
    return {"titulo": titulo, "estado": estado, "detalle": detalle, "solucion": solucion}


def _claude_instalado() -> dict:
    if sys.platform != "win32":
        return _paso("Claude Desktop instalado", AVISO, "Este equipo no es Windows: no se comprueba la instalación.")
    local = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    formas = []
    if (local / "AnthropicClaude").exists():
        formas.append("instalador normal")
    if list((local / "Packages").glob("Claude_*")):
        formas.append("Microsoft Store")
    if formas:
        return _paso("Claude Desktop instalado", OK, "Encontrado (" + " y ".join(formas) + ").")
    return _paso("Claude Desktop instalado", AVISO,
                 "No encontré Claude Desktop en las carpetas habituales.",
                 "Instálalo desde https://claude.ai/download. La web (claude.ai) no puede usar programas de tu PC.")


def _claude_abierto() -> bool | None:
    if sys.platform != "win32":
        return None
    try:
        salida = subprocess.run(["tasklist", "/FI", "IMAGENAME eq claude.exe", "/NH"], capture_output=True,
                                text=True, timeout=10, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return "claude.exe" in salida.stdout.lower()
    except Exception:
        return None


def _configuraciones() -> tuple[list[dict], list[Path]]:
    """Comprueba cada archivo de configuración de Claude. Devuelve los pasos y las carpetas con registro."""
    pasos, registradas = [], []
    for ruta in registrar.rutas_claude():
        tipo = "Microsoft Store" if registrar.es_tienda(ruta) else "Claude Desktop"
        titulo = f"Configuración de {tipo}"
        if not ruta.exists():
            if ruta.parent.exists() or registrar.es_tienda(ruta):
                pasos.append(_paso(titulo, ERROR, f"No existe {ruta}.",
                                   "Pulsa «Conectar con Claude Desktop» en el panel."))
            continue
        try:
            datos = json.loads(ruta.read_text(encoding="utf-8-sig") or "{}")
        except (OSError, ValueError) as error:
            pasos.append(_paso(titulo, ERROR, f"{ruta} no es JSON válido ({error}).",
                               "Claude Desktop no puede leerlo. Corrige el archivo o bórralo y pulsa «Conectar»."))
            continue
        entrada = (datos.get("mcpServers") or {}).get(registrar.NOMBRE) if isinstance(datos, dict) else None
        if not entrada:
            pasos.append(_paso(titulo, ERROR, f"{ruta} existe, pero MCP AutoCAD no está registrado ahí.",
                               "Pulsa «Conectar con Claude Desktop» en el panel."))
            continue
        programa = Path(str(entrada.get("command", "")))
        if not programa.exists():
            pasos.append(_paso(titulo, ERROR, f"Registrado en {ruta}, pero apunta a un programa que no existe: "
                               f"{programa}.", "Pulsa «Conectar con Claude Desktop» para actualizar la ruta."))
            continue
        registradas.append(ruta.parent)
        pasos.append(_paso(titulo, OK, f"Registrado en {ruta}."))
    if not pasos:
        pasos.append(_paso("Configuración de Claude Desktop", ERROR, "No encontré ninguna configuración de Claude.",
                           "Abre Claude Desktop una vez, ciérralo desde la bandeja y pulsa «Conectar»."))
    return pasos, registradas


def _ultimas_lineas(ruta: Path, cuantas: int = 60) -> list[str]:
    try:
        return ruta.read_text(encoding="utf-8", errors="replace").splitlines()[-cuantas:]
    except OSError:
        return []


def _registros(carpetas: list[Path]) -> dict:
    titulo = "Claude intentó arrancar MCP AutoCAD"
    logs = [c / "logs" / LOG for c in carpetas if (c / "logs" / LOG).exists()]
    if not carpetas:
        return _paso(titulo, AVISO, "Sin registro en Claude no se puede comprobar.")
    if not logs:
        return _paso(titulo, ERROR, "Claude Desktop todavía no ha intentado arrancar MCP AutoCAD: no hay "
                     f"registro {LOG}.",
                     "Cierra Claude Desktop desde la bandeja (clic derecho en su icono → Salir) y vuelve a abrirlo. "
                     "Usa el chat de la app instalada, no la web ni otras pestañas.")
    ultimo = max(logs, key=lambda p: p.stat().st_mtime)
    lineas = _ultimas_lineas(ultimo)
    errores = [l.strip() for l in lineas if len(l) < 2000 and _ERRORES.search(l)]
    if errores:
        return _paso(titulo, ERROR, f"Claude lo intentó, pero hubo un error. Último mensaje en {ultimo}: "
                     f"{errores[-1][:300]}", "Mándale este informe a quien te da soporte.")
    return _paso(titulo, OK, f"Sí, sin errores recientes ({ultimo}).")


def diagnosticar(probar_servidor: bool = True) -> dict:
    pasos = [_paso("MCP AutoCAD", OK, f"Versión {__version__} (servidor original {VERSION_ORIGINAL}).")]
    pasos.append(_claude_instalado())
    config, registradas = _configuraciones()
    pasos += config
    pasos.append(_registros(registradas))
    abierto = _claude_abierto()
    if abierto:
        pasos.append(_paso("Claude Desktop abierto", AVISO, "Claude Desktop está abierto ahora.",
                           "Si acabas de conectar o cambiar algo, ciérralo desde la bandeja y vuelve a abrirlo."))
    if probar_servidor:
        r = probar.probar()
        pasos.append(_paso("El servidor responde", OK if r["ok"] else ERROR, r["mensaje"],
                           "" if r["ok"] else "Abre AutoCAD (no LT) con un dibujo y vuelve a probar."))
    primero = next((p for p in pasos if p["estado"] == ERROR), None) or next(
        (p for p in pasos if p["estado"] == AVISO and p["solucion"]), None)
    if primero is None:
        resumen = "Todo está bien. Si Claude aún no ve las herramientas, reinicia Claude Desktop."
    else:
        resumen = f"{primero['titulo']}: {primero['solucion'] or primero['detalle']}"
    return {"ok": not any(p["estado"] == ERROR for p in pasos), "resumen": resumen, "pasos": pasos,
            "informe": informe(pasos)}


def informe(pasos: list[dict]) -> str:
    """Texto para copiar y mandar a soporte."""
    marca = {OK: "[OK]", AVISO: "[AVISO]", ERROR: "[ERROR]"}
    lineas = [f"Diagnóstico de MCP AutoCAD {__version__} ({sys.platform})"]
    for p in pasos:
        lineas.append(f"{marca[p['estado']]} {p['titulo']}: {p['detalle']}")
        if p["solucion"]:
            lineas.append(f"        Qué hacer: {p['solucion']}")
    return "\n".join(lineas)


def main() -> int:
    resultado = diagnosticar()
    print(resultado["informe"])
    print("\n" + resultado["resumen"])
    return 0 if resultado["ok"] else 1
