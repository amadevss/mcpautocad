"""La documentación acompaña a cada versión."""

import importlib.util
from pathlib import Path

from mcpautocad import __version__

RAIZ = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("notas_release", RAIZ / "scripts" / "notas_release.py")
notas_release = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(notas_release)


def test_la_version_actual_esta_en_el_changelog():
    changelog = (RAIZ / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"## [{__version__}]" in changelog, "Añade a CHANGELOG.md el apartado de la versión nueva"
    assert notas_release.novedades(__version__, changelog)


def test_notas_del_release():
    notas = notas_release.notas(__version__)
    assert notas.startswith(f"## ✨ Novedades de la {__version__}")
    assert "¿Qué descargo?" in notas
    assert "](docs/" not in notas  # enlaces relativos convertidos
    assert "](https://github.com/amadevss/mcpautocad/blob/main/docs/GUIA.md)" in notas


def test_version_sin_apartado_solo_lleva_las_instrucciones():
    assert notas_release.notas("9.9.9").startswith("## ⬇️ ¿Qué descargo?")


def test_las_imagenes_del_readme_y_la_guia_existen():
    import re

    for doc, base in ((RAIZ / "README.md", RAIZ), (RAIZ / "docs" / "GUIA.md", RAIZ / "docs")):
        texto = doc.read_text(encoding="utf-8")
        for ruta in re.findall(r'src(?:set)?="((?:docs/)?img/[^"]+)"', texto):
            assert (base / ruta).exists(), f"{doc.name}: falta {ruta}"
