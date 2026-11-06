# Plan de MCP AutoCAD

Objetivo final: que cualquier persona use Claude (web, escritorio o móvil) para dibujar en su AutoCAD con la
misma experiencia que [activecolabmcp](https://github.com/amadevss/activecolabmcp): pegar una URL en Claude,
pulsar **Conectar**, iniciar sesión y listo. Todo en español y simple para el usuario final.

Base técnica: [AutoCAD MCP Pro](https://github.com/U-C4N/Autocad-MCP) (`autocad-mcp-pro`, MIT, Umutcan
Edizsalan), usado como dependencia sin copiar su código. Tiene dos motores: **COM** (AutoCAD real en Windows)
y **ezdxf** (sin AutoCAD, en cualquier sistema).

## Fase 1: versión local para Windows ✅ (esta entrega)

- [x] `mcpautocad.exe` con Python incluido (PyInstaller, modo carpeta para que arranque rápido).
- [x] Instalador Inno Setup por usuario (sin administrador) que se registra solo en Claude Desktop
      (incluida la versión de Microsoft Store) y se quita al desinstalar.
- [x] `mcpautocad servidor`: lee `%APPDATA%\mcpautocad\config.json`, pone `AUTOCAD_MCP_BACKEND=com`,
      `TOOL_PROFILE`, `TOOL_PACKS`, `DISCOVERY_MODE`, `ENABLE_3D`, `DANGEROUS_COMMANDS_ENABLED=false` y arranca el
      servidor original por stdio.
- [x] Panel local `http://localhost:8765`: modo (Completo/Ligero/Búsqueda), paquetes, 3D, atajos, contador de
      tokens medido sobre el servidor real (`scripts/medir_tokens.py` → `catalogo.json`).
- [x] Tests en Linux con ezdxf; GitHub Actions construye en `windows-latest`, prueba el `.exe` y lo publica.

Cifras medidas (v1.7.0, tokens ≈ caracteres/4):

| Configuración | Herramientas | Tokens |
|---|---|---|
| Completo, todos los paquetes | 241 (243 en el original) | ~97.300 |
| + 3D | 246 (248) | ~98.650 |
| Completo, solo Básico | 182 (184) | ~67.000 |
| Ligero, todos los paquetes | 66 | ~27.600 |
| Ligero, solo Básico | 56 | ~20.400 |
| Búsqueda | 3 | ~550 |

Las cifras sin paréntesis descuentan `system_run_command` y `system_run_lisp`, que vienen apagadas por defecto.

### Pendiente de la fase 1

- [ ] Pruebas con AutoCAD real (lista de pasos en el README / entrega).
- [ ] Firma de código del `.exe` (quita el aviso de SmartScreen). Opciones: certificado OV/EV o Azure Trusted Signing.
- [x] Icono propio (`scripts/generar_icono.py`): `.exe`, instalador, panel y extensión.
- [x] Extensión `.mcpb` de Claude Desktop (tipo `binary`, solo Windows) con el mismo `.exe` dentro. Su formulario
      (modo como texto, paquetes y 3D como casillas) llega por variables `MCPAUTOCAD_*`. El formato no admite
      listas desplegables ni enlazar al panel.
- [ ] Probar la extensión `.mcpb` en Claude Desktop real (instalar, configurar, desactivar/activar).

## Fase 2: panel avanzado

- [x] Activar o desactivar herramientas una por una (`"desactivadas"` en `config.json`; en la extensión .mcpb,
      un campo de texto con nombres separados por comas). `iniciar.py` las borra del registro de FastMCP
      (`mcp.local_provider.remove_tool`) antes de `mcp.run()`: no se anuncian ni se pueden llamar, tampoco
      desde `call_tool` en modo Búsqueda. `system_status` no se puede apagar.
- [x] Buscador por nombre o descripción, con los tokens de cada herramienta (descripciones del original, en inglés).
- [x] Botón "Probar conexión con AutoCAD" (y `mcpautocad probar`): arranca el servidor como Claude y llama a
      `system_status`. Ojo: si AutoCAD está cerrado, el original lo abre (`Dispatch`), así que la prueba puede tardar.
- [x] Sin banner ni búsqueda de actualizaciones de fastmcp al arrancar (`FASTMCP_SHOW_SERVER_BANNER`,
      `FASTMCP_CHECK_FOR_UPDATES`).
- [x] Aviso de versión nueva en el panel (`actualizaciones.py`: consulta el último Release de GitHub, guarda la
      respuesta 6 horas y no avisa si no hay internet). En una etiqueta `v*`, el workflow comprueba que coincide con
      `__version__`.
- [x] Descripciones del panel en español (`traducciones.json`). Claude sigue viendo las originales en inglés. Un test
      avisa de las herramientas nuevas sin traducir al subir de versión el original.

## Fase 3: servicio en el VPS (Docker)

URL que se pega en Claude como **conector personalizado**.

- `system_run_command` y `system_run_lisp` apagadas por defecto también en el servicio (ya lo están en local).
- Mismo servidor original con transporte HTTP (`--transport http`). Ojo: el original exige
  `ALLOW_REMOTE_HTTP` y `MCP_AUTH_TOKEN` para escuchar fuera de localhost; delante irá nuestra capa OAuth.
- **OAuth 2.1** con inicio de sesión de Google (como en activecolabmcp): descubrimiento
  `/.well-known/oauth-authorization-server`, registro dinámico de clientes, PKCE.
- **Caddy** con HTTPS automático, **Redis** para sesiones, tokens y emparejamientos.
- **Un proceso o sesión aislada por usuario**: el original guarda el dibujo activo en memoria del proceso, así
  que no se puede compartir un único proceso entre usuarios.
- Archivos por usuario (`ALLOWED_PATHS` apuntando a su carpeta) con enlaces de descarga firmados y caducidad.
- Sin AutoCAD conectado → motor **ezdxf** en la nube (dibuja DXF/PDF descargables).
- El panel de configuración pasa a ser web (mismas opciones, por usuario).
- Límites por usuario (tiempo de CPU, tamaño de archivos), registros y copias de seguridad.

## Fase 4: puente con el AutoCAD de cada usuario

Para que Claude (web, escritorio o móvil) dibuje en el AutoCAD del PC del usuario a través del VPS.

- El mismo `mcpautocad.exe` gana una orden `puente`: abre un **WebSocket saliente** hacia el VPS (sin abrir
  puertos en el PC ni tocar el firewall).
- **Emparejamiento**: el usuario inicia sesión en la web, recibe un código corto (p. ej. `K7Q-4MX`) y lo
  escribe en el panel local. El VPS asocia ese equipo a su cuenta; el puente guarda un token renovable.
- El VPS reenvía las llamadas MCP del usuario por el WebSocket; el puente las ejecuta con el motor COM
  localmente y devuelve el resultado. Si el puente no está conectado, se usa ezdxf en la nube y Claude lo avisa.
- Reconexión automática, latido, cola con tiempo de espera, y aviso en el panel ("Conectado al servicio").
- Seguridad: solo conexiones salientes TLS, modo sin restricciones (`DANGEROUS_COMMANDS_ENABLED`) siempre apagado y `system_run_command` / `system_run_lisp` apagadas por defecto en el puente, el usuario puede pausar
  el puente desde la bandeja del sistema.

## Decisiones tomadas

- No copiamos código del original: dependencia fija `autocad-mcp-pro[com,pdf,office]==1.7.0`. Al subir de
  versión: cambiar `pyproject.toml` y `VERSION_ORIGINAL`, ejecutar `scripts/medir_tokens.py` y los tests.
- La configuración del panel siempre manda sobre variables de entorno externas, para que lo que ve el usuario
  sea lo que ve Claude.
- Modo por defecto: **Ligero** con todos los paquetes (66 herramientas, ~27.600 tokens).
- PyInstaller en modo carpeta (no un único archivo): arranca más rápido y da menos falsos positivos de antivirus.
