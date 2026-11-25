# Cambios

Todas las versiones de MCP AutoCAD, de la más nueva a la más antigua. Las descargas están en
[Releases](https://github.com/amadevss/mcpautocad/releases).

## [0.2.0] - 2026-11-25

### Nuevo
- **App rediseñada** con tres pestañas: **Inicio** (conexión, primeros pasos y ejemplos para copiar),
  **Herramientas** (modo, paquetes y herramientas una por una) y **Ayuda** (diagnóstico, problemas frecuentes y enlaces).
- **Indicadores de estado** siempre visibles arriba: Claude Desktop (conectado, reinicio pendiente o no conectado),
  AutoCAD (abierto, responde o cerrado) y versión (al día o hay una nueva). Se actualizan solos.
- **Botón «Reiniciar Claude Desktop»**: cierra Claude, también desde la bandeja, y lo vuelve a abrir, siempre
  preguntando antes. Funciona con Claude de Microsoft Store y con el instalador clásico.
- Si pulsas **Conectar** con Claude abierto, la app ofrece **cerrarlo, conectar y volver a abrirlo** sola.
- **Diagnóstico en vivo**: cada comprobación aparece en cuanto termina.
- **Avisos flotantes** que confirman cada acción, **botones que muestran que están trabajando** y una marca
  **«Cambios sin guardar»** con el botón Guardar siempre a mano en la barra inferior.
- Las tarjetas de modo muestran **cuántos tokens y herramientas** supone cada una, y el contador de tokens anima el cambio.
- **Ejemplos de qué pedirle a Claude**, con un botón para copiarlos.
- Documentación nueva: [guía paso a paso](docs/GUIA.md), este registro de cambios y capturas actualizadas.

### Mejorado
- **Instalador más pequeño**: los dos programas comparten el código en lugar de llevar cada uno su copia. El
  instalador baja de 83 a 47 MB, y la versión portátil y la extensión `.mcpb`, de 101 a 76 MB.
- Pulsar el indicador de AutoCAD ya no lanza la prueba (que abre AutoCAD si está cerrado): solo lleva a la tarjeta.
- Si cierras la app con cambios sin guardar, te avisa antes.

## [0.1.2] - 2026-11-19

### Corregido
- **Claude Desktop de Microsoft Store no cargaba MCP AutoCAD.** Claude había movido su configuración a
  `%LOCALAPPDATA%\Claude-Data\…` y el instalador escribía en la carpeta antigua. Ahora se detecta la carpeta que Claude
  usa de verdad.
- La configuración de Claude solo se cambia **con Claude cerrado**, porque Claude la reescribe y borraba el cambio. El
  instalador y la app lo piden.
- Los acentos de la pantalla final del instalador salían mal.

### Mejorado
- El diagnóstico muestra qué carpeta usa Claude, avisa si MCP AutoCAD quedó en una que Claude ya no lee, lee los
  registros en `%LOCALAPPDATA%\Claude\logs` y detecta políticas de empresa.
- Copia de seguridad propia (`.bak-mcpautocad`) antes de cambiar la configuración de Claude.

## [0.1.1] - 2026-11-18

### Nuevo
- Botón **Diagnóstico**: dice por qué Claude no ve las herramientas y deja copiar un informe.
- La app se abre en **su propia ventana** (`MCP AutoCAD.exe`, sin consola) y se cierra al cerrar la ventana.
- Botón **Publicar versión** en GitHub Actions.

## [0.1.0] - 2026-11-18

Primera versión publicada.

- Instalador para Windows con Python incluido, que se conecta solo con Claude Desktop.
- Extensión `.mcpb` y versión portátil `.zip`.
- Panel para elegir modo (Completo, Ligero o Búsqueda), paquetes, 3D y herramientas una por una, con el coste en tokens.
- Descripciones de las 248 herramientas en español y aviso de versión nueva.
- `system_run_command` y `system_run_lisp` apagadas por defecto por seguridad.

[0.2.0]: https://github.com/amadevss/mcpautocad/releases/tag/v0.2.0
[0.1.2]: https://github.com/amadevss/mcpautocad/releases/tag/v0.1.2
[0.1.1]: https://github.com/amadevss/mcpautocad/releases/tag/v0.1.1
[0.1.0]: https://github.com/amadevss/mcpautocad/releases/tag/v0.1.0
