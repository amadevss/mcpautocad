"""Dibuja una planta de ejemplo con las herramientas del servidor y la guarda como imagen.

Usa el servidor real (motor ezdxf, sin AutoCAD), igual que lo haría Claude:
arch_plan_from_spec + guardar DXF. Después convierte el DXF en PNG.

Uso:  python scripts/ilustraciones/plano_ejemplo.py docs/img/ejemplo-plano.png
"""

from __future__ import annotations

import asyncio
import os
import sys
import tempfile
from pathlib import Path

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

PLANTA = {
    "sheet": {"intent": "plan", "sheet_size": "A3", "scale": 50},
    "lang": "en",
    "walls": [
        {"id": "ext", "axis": [[0, 0], [9000, 0], [9000, 6500], [0, 6500]], "thickness": 250,
         "justification": "center", "closed": True},
        {"id": "int1", "axis": [[5000, 0], [5000, 6500]], "thickness": 120, "justification": "center"},
        {"id": "int2", "axis": [[5000, 3500], [9000, 3500]], "thickness": 120, "justification": "center"},
    ],
    "openings": [
        {"id": "P1", "wall": "ext", "kind": "door", "offset": 1500, "width": 900},
        {"id": "P2", "wall": "int1", "kind": "door", "offset": 1800, "width": 800},
        {"id": "P3", "wall": "int2", "kind": "door", "offset": 1200, "width": 800},
        {"id": "V1", "wall": "ext", "kind": "window", "offset": 6200, "width": 1500},
        {"id": "V2", "wall": "ext", "kind": "window", "offset": 10000, "width": 1800},
        {"id": "V4", "wall": "ext", "kind": "window", "offset": 16500, "width": 1500},
        {"id": "V3", "wall": "ext", "kind": "window", "offset": 26500, "width": 1800},
    ],
    "rooms": [
        {"id": "R1", "name": "Sala", "number": "01", "at": [2500, 3250]},
        {"id": "R2", "name": "Dormitorio", "number": "02", "at": [7000, 1750]},
        {"id": "R3", "name": "Cocina", "number": "03", "at": [7000, 5000]},
    ],
    "chains": {"sides": ["bottom", "left"]},
}


async def dibujar(dxf: Path) -> None:
    env = {**os.environ, "AUTOCAD_MCP_BACKEND": "ezdxf", "LOG_LEVEL": "ERROR"}
    transporte = StdioTransport(command=sys.executable, args=["-m", "server"], env=env)
    async with Client(transporte, timeout=120) as cliente:
        await cliente.call_tool("drawing_new", {})
        await cliente.call_tool("arch_plan_from_spec", {"spec": PLANTA})
        await cliente.call_tool("drawing_save_as", {"path": str(dxf)})


def a_png(dxf: Path, png: Path) -> None:
    import ezdxf
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from ezdxf.addons.drawing import Frontend, RenderContext
    from ezdxf.addons.drawing.config import BackgroundPolicy, ColorPolicy, Configuration
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

    doc = ezdxf.readfile(dxf)
    fig = plt.figure(figsize=(12, 8), dpi=150)
    ax = fig.add_axes([0, 0, 1, 1])
    config = Configuration(background_policy=BackgroundPolicy.WHITE, color_policy=ColorPolicy.BLACK)
    Frontend(RenderContext(doc), MatplotlibBackend(ax), config=config).draw_layout(doc.modelspace())
    ax.margins(0.04)
    fig.savefig(png, facecolor="white")


def main() -> None:
    destino = Path(sys.argv[1] if len(sys.argv) > 1 else "ejemplo-plano.png")
    with tempfile.TemporaryDirectory() as carpeta:
        dxf = Path(carpeta) / "plano.dxf"
        asyncio.run(dibujar(dxf))
        a_png(dxf, destino)
    print(f"Imagen guardada en {destino}")


if __name__ == "__main__":
    main()
