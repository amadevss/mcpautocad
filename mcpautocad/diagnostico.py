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


TIPOS = {
    "reubicada": "datos reubicados de Claude Desktop (Microsoft Store)",
    "tienda": "Claude Desktop de Microsoft Store",
    "clasica": "Claude Desktop (instalador clásico)",
    "macos": "Claude Desktop para macOS",
    "linux": "Claude Desktop",
    "forzada": "ruta indicada en MCPAUTOCAD_CLAUDE_CONFIG",
}


def _version_claude() -> str:
    """Versión y familia del paquete de Claude de Microsoft Store (vacío si no hay)."""
    if sys.platform != "win32":
        return ""
    try:
        salida = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-AppxPackage *Claude* | ForEach-Object { $_.Version + ' (' + $_.PackageFamilyName + ')' }"],
            capture_output=True, text=True, timeout=20, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return " / ".join(l.strip() for l in salida.stdout.splitlines() if l.strip())
    except Exception:
        return ""


def _claude_instalado() -> dict:
    if sys.platform != "win32":
        return _paso("Claude Desktop instalado", AVISO, "Este equipo no es Windows: no se comprueba la instalación.")
    local = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    formas = []
    if (local / "AnthropicClaude").exists():
        formas.append("instalador clásico")
    version = _version_claude()
    if version or list((local / "Packages").glob("Claude_*")):
        formas.append("Microsoft Store" + (f" {version}" if version else ""))
    if formas:
        return _paso("Claude Desktop instalado", OK, "Encontrado: " + "; ".join(formas) + ".")
    return _paso("Claude Desktop instalado", AVISO,
                 "No encontré Claude Desktop en las carpetas habituales.",
                 "Instálalo desde https://claude.ai/download. La web (claude.ai) no puede usar programas de tu PC.")


def _configuracion(u: dict) -> tuple[list[dict], bool]:
    """La configuración que usa Claude: dónde está y si MCP AutoCAD está bien registrado ahí."""
    activa = u["activa"]
    pasos = [_paso("Carpeta de configuración de Claude", OK,
                   f"Claude usa {activa} ({TIPOS.get(u['tipo'], u['tipo'])}).")]
    titulo = "MCP AutoCAD registrado en Claude"
    conectar = ("Cierra Claude Desktop por completo (clic derecho en su icono → Salir) y pulsa «Conectar con "
                "Claude Desktop» en el panel.")
    otras = [str(r) for r in u["candidatas"][1:] if registrar.esta_registrado(r)]
    extra = f" Sí está en otra carpeta que Claude ya no lee: {', '.join(otras)}." if otras else ""
    if not activa.exists():
        pasos.append(_paso(titulo, ERROR, f"No existe {activa}.{extra}", conectar))
        return pasos, False
    try:
        datos = json.loads(activa.read_text(encoding="utf-8-sig") or "{}")
    except (OSError, ValueError) as error:
        pasos.append(_paso(titulo, ERROR, f"{activa} no es JSON válido ({error}).",
                           "Claude Desktop no puede leerlo. Corrige el archivo o bórralo y pulsa «Conectar»."))
        return pasos, False
    entrada = (datos.get("mcpServers") or {}).get(registrar.NOMBRE) if isinstance(datos, dict) else None
    if not entrada:
        pasos.append(_paso(titulo, ERROR, f"No está en {activa}.{extra}", conectar))
        return pasos, False
    programa = Path(str(entrada.get("command", "")))
    if not programa.exists():
        pasos.append(_paso(titulo, ERROR, f"Apunta a un programa que no existe: {programa}.", conectar))
        return pasos, False
    pasos.append(_paso(titulo, OK, f"Sí, con {programa}."))
    return pasos, True


def _ultimas_lineas(ruta: Path, cuantas: int = 60) -> list[str]:
    try:
        return ruta.read_text(encoding="utf-8", errors="replace").splitlines()[-cuantas:]
    except OSError:
        return []


def _datos_de_usuario(carpetas: list[Path]) -> str:
    """Lo que dice main.log de dónde guarda Claude sus datos (p. ej. 'relocated_local')."""
    for carpeta in carpetas:
        for linea in reversed(_ultimas_lineas(carpeta / "main.log", 4000)):
            m = re.search(r"user_data_location:\s*'([^']+)'", linea)
            if m:
                return m.group(1)
    return ""


def _registros(carpetas: list[Path], registrado: bool) -> dict:
    titulo = "Claude intentó arrancar MCP AutoCAD"
    logs = [c / LOG for c in carpetas if (c / LOG).exists()]
    if not logs:
        if not registrado:
            return _paso(titulo, AVISO, "Todavía no, porque no está registrado en la configuración que usa Claude.")
        return _paso(titulo, ERROR, f"Todavía no: no hay registro {LOG} en "
                     + ", ".join(str(c) for c in carpetas if c.exists()) + ".",
                     "Cierra Claude Desktop desde la bandeja (clic derecho en su icono → Salir) y vuelve a abrirlo. "
                     "Usa el modo Chat de la app instalada, no la web ni Cowork.")
    ultimo = max(logs, key=lambda p: p.stat().st_mtime)
    errores = [l.strip() for l in _ultimas_lineas(ultimo) if len(l) < 2000 and _ERRORES.search(l)]
    if errores:
        return _paso(titulo, ERROR, f"Claude lo intentó, pero hubo un error. Último mensaje en {ultimo}: "
                     f"{errores[-1][:300]}", "Mándale este informe a quien te da soporte.")
    return _paso(titulo, OK, f"Sí, sin errores recientes ({ultimo}).")


def diagnosticar(probar_servidor: bool = True) -> dict:
    u = registrar.ubicaciones()
    pasos = [_paso("MCP AutoCAD", OK, f"Versión {__version__} (servidor original {VERSION_ORIGINAL}).")]
    pasos.append(_claude_instalado())
    config, registrado = _configuracion(u)
    pasos += config
    ubicacion = _datos_de_usuario(u["logs"])
    if ubicacion:
        pasos.append(_paso("Datos de Claude según su registro", OK, f"user_data_location: {ubicacion}."))
    pasos.append(_registros(u["logs"], registrado))
    reglas = registrar.politicas()
    if reglas:
        pasos.append(_paso("Políticas de empresa", AVISO, "Hay políticas de Claude en el registro de Windows: "
                           + ", ".join(reglas) + ".",
                           "Pueden impedir los servidores locales. Consulta con el administrador de tu equipo."))
    if registrar.claude_abierto():
        pasos.append(_paso("Claude Desktop abierto", AVISO, "Claude Desktop está abierto ahora.",
                           "Para conectar o cambiar algo, ciérralo antes desde la bandeja; después vuelve a abrirlo."))
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
