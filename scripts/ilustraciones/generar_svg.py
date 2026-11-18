"""Genera las ilustraciones SVG del README en docs/img/.

- banner.svg                       cabecera
- como-funciona-{claro,oscuro}.svg diagrama Claude → MCP AutoCAD → AutoCAD
- tokens-{claro,oscuro}.svg        gráfica de tokens por modo (cifras del catálogo real)
- boton-*.svg                      botones de descarga

Uso:  python scripts/ilustraciones/generar_svg.py
"""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from mcpautocad import catalogo  # noqa: E402

DESTINO = RAIZ / "docs" / "img"
FUENTE = "-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"

TEMAS = {
    "claro": {"fondo": "#ffffff", "tarjeta": "#f6f8fa", "borde": "#d0d7de", "texto": "#1f2328",
              "suave": "#59636e", "acento": "#c8102e", "acento_suave": "#fde8eb", "rejilla": "#e6e9ed"},
    "oscuro": {"fondo": "#0d1117", "tarjeta": "#161b22", "borde": "#30363d", "texto": "#e6edf3",
               "suave": "#9198a1", "acento": "#f2405a", "acento_suave": "#3a1d23", "rejilla": "#262c34"},
}


def mira(x: float, y: float, lado: float, color="#c8102e") -> str:
    """El icono del proyecto (cuadrado redondeado con mira de CAD)."""
    c, g = lado / 2, lado * 0.07
    caja, largo, hueco = lado * 0.13, lado * 0.36, lado * 0.19
    lineas = [(c - largo, c, c - hueco, c), (c + hueco, c, c + largo, c),
              (c, c - largo, c, c - hueco), (c, c + hueco, c, c + largo)]
    return (f'<g transform="translate({x} {y})">'
            f'<rect x="{lado*0.04}" y="{lado*0.04}" width="{lado*0.92}" height="{lado*0.92}" rx="{lado*0.2}" fill="{color}"/>'
            f'<rect x="{c-caja}" y="{c-caja}" width="{2*caja}" height="{2*caja}" fill="none" stroke="#fff" stroke-width="{g}"/>'
            + "".join(f'<line x1="{a}" y1="{b}" x2="{cc}" y2="{d}" stroke="#fff" stroke-width="{g}"/>'
                      for a, b, cc, d in lineas)
            + "</g>")


def svg(ancho: int, alto: int, cuerpo: str, titulo: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{ancho}" height="{alto}" '
            f'viewBox="0 0 {ancho} {alto}" role="img" aria-label="{titulo}" font-family="{FUENTE}">'
            f"<title>{titulo}</title>{cuerpo}</svg>\n")


def banner() -> str:
    a, h = 1280, 360
    planta = (  # planta simplificada a la derecha
        '<g transform="translate(860 92)" fill="none" stroke-linecap="square">'
        '<rect x="0" y="0" width="300" height="200" stroke="#ffffff" stroke-width="8"/>'
        '<line x1="165" y1="0" x2="165" y2="200" stroke="#ffffff" stroke-width="5"/>'
        '<line x1="165" y1="95" x2="300" y2="95" stroke="#ffffff" stroke-width="5"/>'
        '<path d="M70 200 v-32 a32 32 0 0 1 32 32" stroke="#f2405a" stroke-width="3"/>'
        '<path d="M165 120 h-30 a30 30 0 0 0 30 30" stroke="#f2405a" stroke-width="3"/>'
        '<line x1="300" y1="125" x2="300" y2="170" stroke="#f2405a" stroke-width="8"/>'
        '<line x1="0" y1="-26" x2="300" y2="-26" stroke="#9198a1" stroke-width="1.5"/>'
        '<line x1="0" y1="-34" x2="0" y2="-18" stroke="#9198a1" stroke-width="1.5"/>'
        '<line x1="300" y1="-34" x2="300" y2="-18" stroke="#9198a1" stroke-width="1.5"/>'
        '<text x="150" y="-34" fill="#9198a1" font-size="16" text-anchor="middle" stroke="none">9 000</text>'
        '<text x="82" y="108" fill="#e6edf3" font-size="18" stroke="none">Sala</text>'
        '<text x="182" y="52" fill="#e6edf3" font-size="18" stroke="none">Cocina</text>'
        '<text x="182" y="150" fill="#e6edf3" font-size="18" stroke="none">Dormitorio</text>'
        "</g>")
    burbuja = (
        '<g transform="translate(560 120)">'
        '<rect width="250" height="104" rx="18" fill="#21262d" stroke="#30363d"/>'
        '<path d="M249 40 l24 12 l-24 12 z" fill="#21262d"/>'
        '<text x="22" y="40" fill="#e6edf3" font-size="19">«Dibuja una planta</text>'
        '<text x="22" y="66" fill="#e6edf3" font-size="19">de 9 × 6,5 m con sala,</text>'
        '<text x="22" y="92" fill="#e6edf3" font-size="19">cocina y dormitorio»</text>'
        "</g>")
    cuerpo = (
        '<defs><linearGradient id="f" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#1b1f27"/><stop offset="1" stop-color="#0d1117"/></linearGradient></defs>'
        f'<rect width="{a}" height="{h}" rx="20" fill="url(#f)"/>'
        + mira(64, 72, 96)
        + '<text x="64" y="232" fill="#ffffff" font-size="58" font-weight="700">MCP AutoCAD</text>'
        '<text x="64" y="276" fill="#e6edf3" font-size="25">Pídele a Claude que dibuje en tu AutoCAD</text>'
        '<text x="64" y="314" fill="#9198a1" font-size="18">Windows · AutoCAD (no LT) · Claude Desktop · En español</text>'
        + burbuja + planta)
    return svg(a, h, cuerpo, "MCP AutoCAD: pídele a Claude que dibuje en tu AutoCAD")


def flecha(x1, x2, y, color, texto, t) -> str:
    return (f'<line x1="{x1}" y1="{y}" x2="{x2-10}" y2="{y}" stroke="{color}" stroke-width="3"/>'
            f'<path d="M{x2} {y} l-14 -8 v16 z" fill="{color}"/>'
            f'<text x="{(x1+x2)/2}" y="{y-14}" fill="{t["suave"]}" font-size="16" text-anchor="middle">{texto}</text>')


def tarjeta(x, y, w, h, t, titulo, lineas, icono="") -> str:
    texto = "".join(f'<text x="{x+24}" y="{y+108+i*26}" fill="{t["suave"]}" font-size="17">{l}</text>'
                    for i, l in enumerate(lineas))
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{t["tarjeta"]}" stroke="{t["borde"]}"/>'
            + icono +
            f'<text x="{x+24}" y="{y+72}" fill="{t["texto"]}" font-size="22" font-weight="700">{titulo}</text>' + texto)


def como_funciona(t: dict) -> str:
    a, h = 1200, 330
    y, w, alto = 40, 320, 230
    xs = [20, 440, 860]
    ic = t["acento"]
    iconos = [
        f'<rect x="{xs[0]+24}" y="{y+18}" width="34" height="26" rx="8" fill="none" stroke="{ic}" stroke-width="3"/>'
        f'<path d="M{xs[0]+34} {y+44} l-4 9 l12 -9" fill="{ic}"/>',
        mira(xs[1] + 22, y + 14, 36, ic),
        f'<rect x="{xs[2]+24}" y="{y+16}" width="38" height="30" fill="none" stroke="{ic}" stroke-width="3"/>'
        f'<line x1="{xs[2]+43}" y1="{y+16}" x2="{xs[2]+43}" y2="{y+46}" stroke="{ic}" stroke-width="2"/>',
    ]
    cuerpo = (
        f'<rect width="{a}" height="{h}" rx="20" fill="{t["fondo"]}"/>'
        + tarjeta(xs[0], y, w, alto, t, "1. Le pides a Claude",
                  ["En Claude Desktop, con tus", "palabras: «dibuja un", "rectángulo de 100 × 50»."], iconos[0])
        + tarjeta(xs[1], y, w, alto, t, "2. MCP AutoCAD",
                  ["El programa de tu PC traduce", "la petición en órdenes de", "AutoCAD. Tú eliges qué ve Claude."],
                  iconos[1])
        + tarjeta(xs[2], y, w, alto, t, "3. AutoCAD dibuja",
                  ["En tu dibujo abierto, en vivo.", "Claude revisa el resultado y", "te lo cuenta."], iconos[2])
        + flecha(xs[0] + w + 8, xs[1] - 8, y + alto / 2, ic, "pide", t)
        + flecha(xs[1] + w + 8, xs[2] - 8, y + alto / 2, ic, "dibuja", t)
        + f'<text x="{a/2}" y="{h-18}" fill="{t["suave"]}" font-size="16" text-anchor="middle">'
          "El programa y AutoCAD trabajan en tu PC. Claude recibe solo lo que las herramientas le responden.</text>")
    return svg(a, h, cuerpo, "Cómo funciona: Claude Desktop, MCP AutoCAD y AutoCAD")


def tokens(t: dict) -> str:
    modos = [("Completo", {"modo": "completo"}), ("Ligero (recomendado)", {"modo": "ligero"}),
             ("Búsqueda", {"modo": "busqueda"})]
    datos = [(n, catalogo.estimar(c)) for n, c in modos]
    a, h = 1000, 300
    x0, ancho_max, y0, alto_barra, paso = 250, 560, 92, 34, 62
    maximo = max(e["tokens"] for _, e in datos)
    cuerpo = [f'<rect width="{a}" height="{h}" rx="20" fill="{t["fondo"]}"/>',
              f'<text x="32" y="46" fill="{t["texto"]}" font-size="22" font-weight="700">'
              "Tokens que ocupan las herramientas en cada conversación</text>",
              f'<text x="32" y="72" fill="{t["suave"]}" font-size="15">Aproximado (caracteres ÷ 4), medido sobre '
              "el servidor real. Menos tokens = conversaciones más largas.</text>"]
    for i, (nombre, e) in enumerate(datos):
        y = y0 + i * paso
        largo = max(4, ancho_max * e["tokens"] / maximo)
        r = min(4, largo / 2)
        cuerpo.append(f'<text x="{x0-16}" y="{y+16}" fill="{t["texto"]}" font-size="17" font-weight="600" '
                      f'text-anchor="end">{nombre}</text>')
        cuerpo.append(f'<text x="{x0-16}" y="{y+36}" fill="{t["suave"]}" font-size="14" text-anchor="end">'
                      f'Claude ve {e["herramientas"]} herramientas</text>')
        # barra con el extremo de datos redondeado y anclada a la línea base
        cuerpo.append(f'<path d="M{x0} {y} h{largo-r} a{r} {r} 0 0 1 {r} {r} v{alto_barra-2*r} '
                      f'a{r} {r} 0 0 1 -{r} {r} h-{largo-r} z" fill="{t["acento"]}"/>')
        redondeo = 100 if e["tokens"] >= 1000 else 10
        valor = f"{round(e['tokens'] / redondeo) * redondeo:,}".replace(",", ".")
        cuerpo.append(f'<text x="{x0+largo+12}" y="{y+23}" fill="{t["texto"]}" font-size="17" '
                      f'font-weight="600">≈ {valor}</text>')
    cuerpo.append(f'<line x1="{x0}" y1="{y0-10}" x2="{x0}" y2="{y0+2*paso+alto_barra+10}" '
                  f'stroke="{t["suave"]}" stroke-width="1"/>')
    return svg(a, h, "".join(cuerpo), "Tokens por modo: Completo, Ligero y Búsqueda")


def boton(texto: str, sub: str, principal: bool) -> str:
    a, h = 340, 72
    fondo = "#c8102e" if principal else "#2d333b"
    flecha_svg = ('<g transform="translate(24 20)" fill="none" stroke="#fff" stroke-width="3" '
                  'stroke-linecap="round" stroke-linejoin="round">'
                  '<path d="M16 2 v20 M7 14 l9 9 l9 -9 M3 30 h26"/></g>')
    cuerpo = (f'<rect width="{a}" height="{h}" rx="14" fill="{fondo}"/>' + flecha_svg
              + f'<text x="72" y="33" fill="#fff" font-size="20" font-weight="700">{texto}</text>'
              f'<text x="72" y="55" fill="#ffffffcc" font-size="14">{sub}</text>')
    return svg(a, h, cuerpo, texto)


def main() -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)
    archivos = {"banner.svg": banner(),
                "boton-instalador.svg": boton("Descargar instalador", "Windows · recomendado", True),
                "boton-extension.svg": boton("Extensión .mcpb", "para Claude Desktop", False),
                "boton-portatil.svg": boton("Versión portátil .zip", "sin instalar", False)}
    for nombre, t in TEMAS.items():
        archivos[f"como-funciona-{nombre}.svg"] = como_funciona(t)
        archivos[f"tokens-{nombre}.svg"] = tokens(t)
    for nombre, contenido in archivos.items():
        (DESTINO / nombre).write_text(contenido, encoding="utf-8")
        print("  ", DESTINO / nombre)


if __name__ == "__main__":
    main()
