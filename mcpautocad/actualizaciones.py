"""Aviso de versión nueva: consulta el último Release publicado en GitHub.

Solo hace una petición de lectura a la API pública de GitHub, sin enviar nada
del usuario. Si no hay internet o no hay Releases, no avisa de nada.
"""

from __future__ import annotations

import json
import re
import time
import urllib.request

from . import __version__

REPOSITORIO = "amadevss/mcpautocad"
URL_API = f"https://api.github.com/repos/{REPOSITORIO}/releases/latest"
URL_RELEASES = f"https://github.com/{REPOSITORIO}/releases"
_CACHE: dict = {}
_DURACION_CACHE = 6 * 3600  # segundos


def clave_version(texto: str) -> tuple:
    """Convierte '0.1.0', 'v0.2.0' o '0.1.0-dev.4' en algo comparable.

    Una versión de prueba (con guion) va antes que la final con el mismo número.
    """
    texto = texto.strip().lstrip("vV")
    base, _, extra = texto.partition("-")
    numeros = tuple(int(n) for n in re.findall(r"\d+", base)[:3])
    numeros += (0,) * (3 - len(numeros))
    return numeros + ((0, extra) if extra else (1, ""))


def _ultimo_release(timeout: float) -> dict:
    peticion = urllib.request.Request(URL_API, headers={
        "Accept": "application/vnd.github+json", "User-Agent": "mcpautocad-panel"})
    with urllib.request.urlopen(peticion, timeout=timeout) as respuesta:
        return json.loads(respuesta.read())


def comprobar(actual: str = __version__, timeout: float = 5, consultar=None) -> dict:
    """Devuelve {actual, ultima, hay_nueva, url}. Nunca lanza errores."""
    consultar = consultar or _ultimo_release
    ahora = time.time()
    if _CACHE.get("hasta", 0) > ahora and _CACHE.get("actual") == actual:
        return _CACHE["resultado"]
    resultado = {"actual": actual, "ultima": None, "hay_nueva": False, "url": URL_RELEASES}
    try:
        release = consultar(timeout)
        etiqueta = str(release.get("tag_name") or "")
        if etiqueta and not release.get("draft") and not release.get("prerelease"):
            resultado["ultima"] = etiqueta.lstrip("vV")
            resultado["hay_nueva"] = clave_version(etiqueta) > clave_version(actual)
            resultado["url"] = release.get("html_url") or URL_RELEASES
    except Exception:  # sin internet, sin Releases (404), límite de la API…
        pass
    _CACHE.update(hasta=ahora + _DURACION_CACHE, actual=actual, resultado=resultado)
    return resultado
