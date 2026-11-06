"""Prueba de conexión: arranca el servidor como lo haría Claude y le pide el estado.

La usa el botón "Probar conexión con AutoCAD" del panel. También funciona desde
la línea de comandos:  mcpautocad probar
"""

from __future__ import annotations

import asyncio
import os
import sys

from . import configuracion, registrar

#: Segundos. Si AutoCAD está cerrado, el servidor original lo abre en la primera
#: llamada, y AutoCAD puede tardar un par de minutos en arrancar.
TIEMPO_MAXIMO = 180


async def _estado(cfg: dict) -> dict:
    from fastmcp import Client
    from fastmcp.client.transports import StdioTransport

    comando = registrar.comando()
    entorno = {**os.environ, "LOG_LEVEL": "ERROR"}
    # La prueba no debe depender de las herramientas apagadas a mano.
    for nombre in [n for n in entorno if n.startswith("MCPAUTOCAD_") and n != "MCPAUTOCAD_CONFIG"]:
        del entorno[nombre]
    entorno.update({
        "MCPAUTOCAD_ORIGEN": configuracion.ORIGEN_MCPB,  # lee la config de estas variables
        "MCPAUTOCAD_MODO": "ligero",
        "MCPAUTOCAD_MOTOR": cfg["motor"],
    })
    with open(os.devnull, "w") as silencio:  # sin los registros del servidor en la consola del panel
        transporte = StdioTransport(command=comando["command"], args=comando["args"], env=entorno,
                                    log_file=silencio)
        async with Client(transporte, timeout=TIEMPO_MAXIMO) as cliente:
            resultado = await cliente.call_tool("system_status", {})
    return resultado.structured_content or {}


def resumir(estado: dict, motor_pedido: str = "com") -> dict:
    """Convierte la respuesta de system_status en un mensaje en español."""
    motor = estado.get("backend", "none")
    conectado = bool(estado.get("connected"))
    respuesta = {
        "ok": conectado,
        "motor": motor,
        "version_autocad": estado.get("autocad_version"),
        "documento": estado.get("active_document"),
        "abiertos": estado.get("open_documents"),
        "herramientas": estado.get("tool_count"),
    }
    if not conectado:
        error = estado.get("error") or "AutoCAD no respondió."
        respuesta["mensaje"] = (f"No se pudo conectar con AutoCAD ({error}). Abre AutoCAD (no LT) con un "
                                "dibujo y vuelve a intentarlo.")
    elif motor == "com":
        partes = ["AutoCAD responde."]
        if respuesta["version_autocad"]:
            partes.append(f"Versión: {respuesta['version_autocad']}.")
        if respuesta["documento"]:
            partes.append(f"Dibujo activo: {respuesta['documento']} ({respuesta['abiertos']} abiertos).")
        else:
            partes.append("No hay ningún dibujo abierto: abre o crea uno.")
        respuesta["mensaje"] = " ".join(partes)
    elif motor_pedido == "com":
        # Fuera de Windows el original cambia solo al motor sin AutoCAD.
        respuesta["ok"] = False
        respuesta["mensaje"] = ("Este equipo no puede controlar AutoCAD (hace falta Windows): el servidor "
                                "funciona, pero solo dibuja archivos DXF sin AutoCAD.")
    else:
        respuesta["mensaje"] = "El servidor funciona con el motor sin AutoCAD (ezdxf): dibuja archivos DXF."
    return respuesta


def probar(cfg: dict | None = None) -> dict:
    cfg = configuracion.normalizar(configuracion.cargar() if cfg is None else cfg)
    try:
        return resumir(asyncio.run(_estado(cfg)), cfg["motor"])
    except Exception as error:  # el servidor no arrancó, tardó demasiado, etc.
        return {"ok": False, "motor": cfg["motor"],
                "mensaje": f"El servidor no respondió ({type(error).__name__}: {error})."}


def main() -> int:
    resultado = probar()
    print(resultado["mensaje"])
    return 0 if resultado["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
