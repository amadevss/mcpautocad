# MCP AutoCAD para Claude

Conecta **Claude Desktop** con tu **AutoCAD** en Windows. Le pides a Claude "dibuja una planta de 8 × 6 m con
dos habitaciones" y él dibuja en tu AutoCAD.

Incluye un **panel** sencillo para elegir qué herramientas ve Claude y así gastar menos tokens.

> Se basa en el proyecto de código abierto **[AutoCAD MCP Pro](https://github.com/U-C4N/Autocad-MCP)**
> (paquete `autocad-mcp-pro` 1.7.0), creado por **Umutcan Edizsalan**, con licencia MIT.
> Todo el trabajo de dibujo es suyo; este proyecto lo empaqueta, lo configura y lo instala en español.

---

## 1. Instalar

**Necesitas:** Windows 10/11 (64 bits), AutoCAD (no LT) y [Claude Desktop](https://claude.ai/download).
No necesitas instalar Python: va incluido.

1. Cierra Claude Desktop por completo: clic derecho en su icono de la bandeja del sistema (junto al reloj) → *Salir*.
2. Descarga `Instalar-MCP-AutoCAD-x.y.z.exe` desde la página de
   [Releases](https://github.com/amadevss/mcpautocad/releases) (o desde GitHub Actions, ver más abajo).
3. Ábrelo. Si Windows muestra "Windows protegió su PC", pulsa **Más información → Ejecutar de todas formas**.
   El aviso sale porque el programa todavía no está firmado digitalmente.
4. Sigue el asistente. No pide permisos de administrador. Al terminar:
   - MCP AutoCAD queda **conectado con Claude Desktop** automáticamente.
   - Se abre el **panel** en tu navegador.
5. Abre AutoCAD y después abre Claude Desktop.

**Como extensión de Claude Desktop (.mcpb):** descarga `MCP-AutoCAD-x.y.z.mcpb` y haz doble clic (o arrástralo a
Claude Desktop → Configuración → Extensiones) y pulsa **Instalar**. La configuración se elige en el propio
formulario de la extensión (ver abajo). No hace falta el instalador.

> Usa **una sola** de las dos formas (instalador o extensión). Si usas las dos, Claude verá las herramientas
> repetidas.

**Sin instalar (portátil):** descomprime `MCP-AutoCAD-portatil-x.y.z.zip` en una carpeta fija (por ejemplo
`C:\MCP-AutoCAD`), haz doble clic en `mcpautocad.exe` y pulsa **Conectar con Claude Desktop** en el panel.

## 2. Comprobar que funciona

1. En Claude Desktop, abre una conversación nueva.
2. Pulsa el botón de herramientas (el icono de controles, debajo del cuadro de texto): debe aparecer **autocad**.
3. Escribe: *"Dime el estado de AutoCAD"* y luego *"Dibuja un rectángulo de 100 × 50 y un círculo de radio 20 en su centro"*.

## 3. El panel: elegir herramientas y ahorrar tokens

Ábrelo desde **Inicio → Panel MCP AutoCAD** (o haciendo doble clic en `mcpautocad.exe`).
Se abre en `http://localhost:8765`, solo en tu equipo.

Cada herramienta que Claude ve ocupa espacio (tokens) en **cada** conversación. Menos herramientas
significa conversaciones más largas y más baratas.

**Modo** (es lo que más cambia el consumo):

| Modo | Herramientas que ve Claude | Tokens aprox. |
|---|---|---|
| Completo | 243 (248 con 3D) | ~98.000 |
| **Ligero** (recomendado) | 66 | ~27.600 |
| Búsqueda | 3 (con ellas busca y usa las demás) | ~550 |

**Paquetes** (interruptores): Básico (siempre activo), Mecánica, Arquitectura, P&ID, Planta, Configuración y 3D.
En el modo Completo, Básico ya trae 184 herramientas, así que apagar paquetes ahorra menos que cambiar de modo.
El panel muestra en vivo cuántas herramientas y tokens supone tu elección.

**Atajos:** *Solo 2D*, *Arquitectura*, *Mecánica* y *Todo*.

Al pulsar **Guardar**, **reinicia Claude Desktop** (Salir desde la bandeja y volver a abrir) para aplicar los cambios.

> Las cifras de tokens son aproximadas (caracteres ÷ 4) y se midieron sobre el servidor real con
> `scripts/medir_tokens.py`.

**Seguridad:** los comandos peligrosos del original (LISP y comandos arbitrarios) están siempre desactivados
(`DANGEROUS_COMMANDS_ENABLED=false`).

### Configurar la extensión .mcpb

En Claude Desktop → Configuración → Extensiones → **AutoCAD** → *Configurar*:

- **Modo**: escribe `ligero`, `completo` o `busqueda` (si escribes otra cosa se usa `ligero`).
- **Paquetes y 3D**: casillas de sí/no.

Después de cambiarla, desactiva y vuelve a activar la extensión. El formulario de extensiones de Claude no
admite listas desplegables, por eso el modo se escribe.

## 4. Desinstalar

*Configuración de Windows → Aplicaciones → MCP AutoCAD → Desinstalar*. También se quita de Claude Desktop
sin tocar tus otros servidores MCP. La extensión .mcpb se quita desde Claude Desktop → Configuración → Extensiones.

## 5. Problemas frecuentes

| Problema | Solución |
|---|---|
| No aparece "autocad" en Claude | Sal de Claude Desktop desde la bandeja (no basta con cerrar la ventana) y vuelve a abrirlo. En el panel, revisa que diga "Conectado". |
| Claude dice que no encuentra AutoCAD | Abre AutoCAD **antes** de pedirle algo y deja un dibujo abierto. AutoCAD LT no sirve (no tiene la interfaz COM). |
| Claude Desktop de Microsoft Store | Se detecta solo. Si no funciona, pulsa **Conectar con Claude Desktop** en el panel. |
| Las herramientas 3D no aparecen | Activa 3D y usa el modo Completo o Búsqueda (el modo Ligero no las incluye). |
| Ver qué pasa por dentro | Abre el registro `%APPDATA%\Claude\logs\mcp-server-autocad.log` (o Claude Desktop → Configuración → Desarrollador). |

Archivos que usa el programa:

- Configuración del panel: `%APPDATA%\mcpautocad\config.json`
- Claude Desktop: `%APPDATA%\Claude\claude_desktop_config.json` (antes de cambiarlo se guarda una copia `.bak`).

---

## Para desarrolladores

### Estructura

```
mcpautocad/
  iniciar.py        lee config.json, pone las variables y arranca el servidor original por stdio
  configuracion.py  leer/guardar config.json y traducirlo a variables de entorno
  panel.py          panel local (http.server de la biblioteca estándar) + panel.html
  registrar.py      agrega/quita la entrada "autocad" en claude_desktop_config.json
  catalogo.py       estimación de herramientas y tokens (datos en catalogo.json)
  __main__.py       mcpautocad [panel|servidor|registrar|quitar]
scripts/medir_tokens.py   regenera catalogo.json midiendo el servidor real
scripts/generar_icono.py  genera los iconos (instalador/, mcpautocad/icono.png y mcpb/icon.png)
scripts/empaquetar_mcpb.py crea la extensión .mcpb (usa @anthropic-ai/mcpb)
mcpb/manifest.json        manifiesto de la extensión (la versión se pone al empaquetar)
mcpautocad.spec           receta de PyInstaller
construir.ps1             construye el .exe y el instalador en Windows
instalador/mcpautocad.iss instalador de Inno Setup
```

### Variables que se pasan al servidor original

| Panel | Variable |
|---|---|
| Modo Completo / Ligero / Búsqueda | `TOOL_PROFILE=full` / `lean` / `full` y `DISCOVERY_MODE=off` / `off` / `search` |
| Paquetes | `TOOL_PACKS=core,mech,arch,pid,plant,settings` (solo los activos; `core` siempre) |
| 3D | `ENABLE_3D=true/false` |
| Motor | `AUTOCAD_MCP_BACKEND=com` (por defecto; `"motor": "ezdxf"` en config.json para trabajar sin AutoCAD) |
| Siempre | `DANGEROUS_COMMANDS_ENABLED=false` |

Con la extensión .mcpb, la configuración llega en variables `MCPAUTOCAD_MODO`, `MCPAUTOCAD_MECANICA`,
`MCPAUTOCAD_ARQUITECTURA`, `MCPAUTOCAD_PID`, `MCPAUTOCAD_PLANTA`, `MCPAUTOCAD_CONFIGURACION` y `MCPAUTOCAD_3D`
(con `MCPAUTOCAD_ORIGEN=mcpb`) y sustituye a `config.json`.

### Probar en cualquier sistema (sin AutoCAD)

Los tests usan el motor **ezdxf**, que no necesita AutoCAD:

```bash
python -m pip install -e ".[dev]"
```

```bash
python -m pytest -q
```

Comprueban la configuración, las variables de entorno, el registro en un `claude_desktop_config.json` de
prueba, el panel, y arrancan el servidor real para contar sus herramientas en cada modo y dibujar una línea.

Abrir el panel en desarrollo:

```bash
python -m mcpautocad panel
```

Al actualizar `autocad-mcp-pro`, cambia la versión en `pyproject.toml` y en `mcpautocad/__init__.py`, y regenera
el catálogo:

```bash
python scripts/medir_tokens.py
```

### Construir el .exe

En Windows con Python 3.11+ ([Inno Setup 6](https://jrsoftware.org/isinfo.php) para el instalador y Node.js
para la extensión .mcpb):

```powershell
powershell -ExecutionPolicy Bypass -File construir.ps1
```

Deja el instalador, el `.zip` portátil y la extensión `.mcpb` en la carpeta `salida`.

### GitHub Actions

El workflow `.github/workflows/construir-exe.yml` se ejecuta en cada push:

1. Pruebas en Linux.
2. En `windows-latest`: construye, vuelve a pasar las pruebas contra el `.exe` empaquetado y sube el resultado
   como artefacto **MCP-AutoCAD-…**.
   Para descargarlo: pestaña **Actions** → la ejecución → sección **Artifacts** (hace falta haber iniciado sesión en GitHub).
3. Si haces push de una etiqueta `v*` (por ejemplo `v0.1.0`), adjunta los archivos a un **Release** público:

```bash
git tag v0.1.0
```

```bash
git push origin v0.1.0
```

## Licencia

MIT. Ver [LICENSE](LICENSE), que incluye el aviso de licencia de
[AutoCAD MCP Pro](https://github.com/U-C4N/Autocad-MCP) © 2026 Umutcan Edizsalan.

El plan de las siguientes fases está en [docs/PLAN.md](docs/PLAN.md).
