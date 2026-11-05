"""Panel local de configuración: http://localhost:8765

Servidor HTTP mínimo (solo biblioteca estándar) que escucha únicamente en
127.0.0.1. Sirve panel.html y una pequeña API JSON.
"""

from __future__ import annotations

import json
import socket
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources

from . import __version__, VERSION_ORIGINAL, catalogo, configuracion, registrar

PUERTO = 8765

PRESETS = {
    "solo2d": {"nombre": "Solo 2D", "paquetes": [], "3d": False},
    "arquitectura": {"nombre": "Arquitectura", "paquetes": ["arquitectura"], "3d": False},
    "mecanica": {"nombre": "Mecánica", "paquetes": ["mecanica"], "3d": False},
    "todo": {"nombre": "Todo", "modo": "completo", "paquetes": list(configuracion.PAQUETES), "3d": True},
}

AVISO_REINICIO = "Reinicia Claude Desktop para aplicar los cambios."


def estado() -> dict:
    cfg = configuracion.cargar()
    rutas = registrar.rutas_claude()
    return {
        "version": __version__,
        "version_original": VERSION_ORIGINAL,
        "config": cfg,
        "ruta_config": str(configuracion.ruta_config()),
        "estimacion": catalogo.estimar(cfg),
        "maximo": catalogo.estimar({"modo": "completo", "paquetes": list(configuracion.PAQUETES), "3d": True}),
        "presets": PRESETS,
        "claude": {
            "registrado": any(registrar.esta_registrado(r) for r in rutas),
            "rutas": [str(r) for r in rutas],
        },
    }


class Manejador(BaseHTTPRequestHandler):
    server_version = "mcpautocad-panel"

    def log_message(self, formato, *args):  # silencioso
        pass

    # --- seguridad: solo peticiones dirigidas a este panel local ---
    def _permitido(self) -> bool:
        puerto = self.server.server_address[1]
        validos = {f"localhost:{puerto}", f"127.0.0.1:{puerto}"}
        if self.headers.get("Host", "") not in validos:
            return False
        origen = self.headers.get("Origin")
        return origen is None or origen in {f"http://{v}" for v in validos}

    def _responder(self, codigo: int, cuerpo: bytes, tipo: str) -> None:
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(cuerpo)

    def _json(self, datos: dict, codigo: int = 200) -> None:
        self._responder(codigo, json.dumps(datos, ensure_ascii=False).encode("utf-8"),
                        "application/json; charset=utf-8")

    def do_GET(self):
        if not self._permitido():
            return self._json({"error": "Prohibido"}, 403)
        if self.path in ("/", "/index.html"):
            html = resources.files(__package__).joinpath("panel.html").read_bytes()
            return self._responder(200, html, "text/html; charset=utf-8")
        if self.path == "/icono.png":
            png = resources.files(__package__).joinpath("icono.png").read_bytes()
            return self._responder(200, png, "image/png")
        if self.path == "/api/estado":
            return self._json(estado())
        self._json({"error": "No encontrado"}, 404)

    def do_POST(self):
        # Exigir JSON evita que otra web envíe formularios a este panel.
        if not self._permitido() or not self.headers.get("Content-Type", "").startswith("application/json"):
            return self._json({"error": "Prohibido"}, 403)
        try:
            largo = min(int(self.headers.get("Content-Length", "0")), 100_000)
            datos = json.loads(self.rfile.read(largo) or b"{}")
        except ValueError:
            return self._json({"error": "JSON inválido"}, 400)

        try:
            if self.path == "/api/estimar":
                return self._json(catalogo.estimar(datos.get("config", {})))
            if self.path == "/api/guardar":
                configuracion.guardar(datos.get("config", {}))
                return self._json({**estado(), "mensaje": "Configuración guardada. " + AVISO_REINICIO})
            if self.path == "/api/registrar":
                rutas = registrar.registrar_en_todas()
                return self._json({**estado(), "mensaje": "Conectado con Claude Desktop. " + AVISO_REINICIO,
                                   "rutas_cambiadas": [str(r) for r in rutas]})
            if self.path == "/api/quitar":
                registrar.quitar_de_todas()
                return self._json({**estado(), "mensaje": "Quitado de Claude Desktop. " + AVISO_REINICIO})
            if self.path == "/api/cerrar":
                self._json({"mensaje": "Panel cerrado. Ya puedes cerrar esta pestaña."})
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                return None
        except registrar.ConfigInvalida as error:
            return self._json({"error": str(error)}, 409)
        self._json({"error": "No encontrado"}, 404)


def _ya_abierto(puerto: int) -> bool:
    """¿Hay ya un panel nuestro escuchando en ese puerto?"""
    try:
        with socket.create_connection(("127.0.0.1", puerto), timeout=0.5) as s:
            s.sendall(f"GET /api/estado HTTP/1.0\r\nHost: 127.0.0.1:{puerto}\r\n\r\n".encode())
            return b"version_original" in s.recv(65536)
    except OSError:
        return False


def crear_servidor(puerto: int = PUERTO) -> ThreadingHTTPServer:
    try:
        return ThreadingHTTPServer(("127.0.0.1", puerto), Manejador)
    except OSError:
        return ThreadingHTTPServer(("127.0.0.1", 0), Manejador)  # puerto ocupado: uno libre


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    abrir = "--sin-navegador" not in argv
    if _ya_abierto(PUERTO):
        url = f"http://localhost:{PUERTO}/"
        print(f"El panel ya está abierto en {url}")
        if abrir:
            webbrowser.open(url)
        return 0
    servidor = crear_servidor()
    url = f"http://localhost:{servidor.server_address[1]}/"
    print(f"Panel de MCP AutoCAD en {url}")
    print("Deja esta ventana abierta mientras usas el panel. Para cerrarlo pulsa Ctrl+C o el botón 'Cerrar panel'.")
    if abrir:
        threading.Timer(0.5, webbrowser.open, args=(url,)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        servidor.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
