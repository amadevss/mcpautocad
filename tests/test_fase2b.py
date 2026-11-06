"""Traducciones del panel y aviso de versión nueva."""

import json
import re
from pathlib import Path

import pytest

from mcpautocad import __version__, actualizaciones, catalogo

RAIZ = Path(__file__).resolve().parents[1]


def test_todas_las_herramientas_tienen_traduccion():
    nombres = {h["nombre"] for h in catalogo.cargar()["herramientas"]}
    es = catalogo.traducciones()
    assert nombres - set(es) == set(), "Herramientas nuevas sin traducir en traducciones.json"
    assert set(es) - nombres == set(), "Traducciones de herramientas que ya no existen"
    assert all(5 < len(t) <= 160 for t in es.values())


def test_el_panel_muestra_la_traduccion_y_guarda_la_original():
    h = {x["nombre"]: x for x in catalogo.herramientas({})}["entity_create_circle"]
    assert h["descripcion"] == "Dibuja un círculo."
    assert h["descripcion_original"].startswith("Create a circle")


@pytest.mark.parametrize("a,b", [
    ("0.1.0", "0.2.0"), ("0.1.0-dev.4", "0.1.0"), ("v0.9.9", "1.0.0"), ("0.1.0", "0.1.1"), ("1.2", "1.2.1"),
])
def test_orden_de_versiones(a, b):
    assert actualizaciones.clave_version(a) < actualizaciones.clave_version(b)


def _release(tag, **extra):
    return lambda timeout: {"tag_name": tag, "html_url": f"https://github.com/x/releases/tag/{tag}", **extra}


def test_avisa_si_hay_una_version_nueva():
    actualizaciones._CACHE.clear()
    r = actualizaciones.comprobar("0.1.0", consultar=_release("v0.2.0"))
    assert r["hay_nueva"] and r["ultima"] == "0.2.0" and r["url"].endswith("v0.2.0")


@pytest.mark.parametrize("consultar", [
    _release("v0.1.0"), _release("v0.0.9"), _release("v9.0.0", prerelease=True), _release("v9.0.0", draft=True),
    lambda timeout: (_ for _ in ()).throw(OSError("sin internet")),
])
def test_no_avisa(consultar):
    actualizaciones._CACHE.clear()
    assert actualizaciones.comprobar("0.1.0", consultar=consultar)["hay_nueva"] is False


def test_la_version_es_la_misma_en_todas_partes():
    pyproject = (RAIZ / "pyproject.toml").read_text(encoding="utf-8")
    assert re.search(r'^version = "(.+)"', pyproject, re.M).group(1) == __version__
