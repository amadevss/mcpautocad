"""Genera el icono de MCP AutoCAD (PNG para la extensión y el panel, ICO para el .exe).

Diseño: cuadrado rojo redondeado con la mira de AutoCAD (cruz con caja de
selección). Uso:  python scripts/generar_icono.py
"""

from pathlib import Path

from PIL import Image, ImageDraw

RAIZ = Path(__file__).resolve().parents[1]
ROJO = (200, 16, 46, 255)
BLANCO = (255, 255, 255, 255)
LADO = 1024  # se dibuja grande y se reduce para que quede suave


def dibujar() -> Image.Image:
    img = Image.new("RGBA", (LADO, LADO), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    m = LADO * 0.04
    d.rounded_rectangle((m, m, LADO - m, LADO - m), radius=LADO * 0.2, fill=ROJO)

    g = round(LADO * 0.07)  # grosor de línea
    c = LADO / 2
    # Mira: cruz larga con hueco central y caja de selección.
    caja = LADO * 0.13
    largo = LADO * 0.36
    d.rectangle((c - caja, c - caja, c + caja, c + caja), outline=BLANCO, width=g)
    hueco = caja + LADO * 0.06
    for x0, y0, x1, y1 in [
        (c - largo, c, c - hueco, c), (c + hueco, c, c + largo, c),
        (c, c - largo, c, c - hueco), (c, c + hueco, c, c + largo),
    ]:
        d.line((x0, y0, x1, y1), fill=BLANCO, width=g)
    return img


def main() -> None:
    img = dibujar()
    destinos = [RAIZ / "instalador" / "icono.png", RAIZ / "mcpautocad" / "icono.png"]
    for destino in destinos:
        img.resize((512, 512), Image.LANCZOS).save(destino)
    img.save(RAIZ / "instalador" / "icono.ico",
             sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("Iconos generados:", *destinos, RAIZ / "instalador" / "icono.ico", sep="\n  ")


if __name__ == "__main__":
    main()
