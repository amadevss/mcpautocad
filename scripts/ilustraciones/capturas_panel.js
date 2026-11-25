// Capturas reales del panel para el README (docs/img/panel-*.png y panel-demo.gif).
//
// Arranca el panel de verdad con una configuración temporal, pulsa sus botones
// como lo haría un usuario y guarda las imágenes. Necesita Node.js con
// Playwright y ffmpeg (para el GIF).
//
// Uso:  node scripts/ilustraciones/capturas_panel.js <python>
//       (<python> = el intérprete con mcpautocad instalado; por defecto "python")

const { chromium } = require("playwright");
const { spawn, execFileSync } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");

const RAIZ = path.resolve(__dirname, "..", "..");
const DESTINO = path.join(RAIZ, "docs", "img");
const PYTHON = process.argv[2] || "python";
const URL = "http://localhost:8765/";
// Las rutas de archivos de este equipo no aportan nada en una captura.
const OCULTAR = "#claude-detalle, footer, .diag small:not(.que) { display: none !important; }";

const esperar = (ms) => new Promise((r) => setTimeout(r, ms));

async function abrirPanel(temporal) {
  fs.mkdirSync(path.join(temporal, "cfg"), { recursive: true });
  fs.writeFileSync(path.join(temporal, "cfg", "config.json"), JSON.stringify({ motor: "ezdxf" }));
  // Un registro de Claude sin errores, para que el diagnóstico de ejemplo salga en verde.
  fs.mkdirSync(path.join(temporal, "Claude", "logs"), { recursive: true });
  fs.writeFileSync(path.join(temporal, "Claude", "logs", "mcp-server-autocad.log"),
    "[autocad] [info] Server started and connected successfully\n");
  const env = {
    ...process.env,
    MCPAUTOCAD_CONFIG: path.join(temporal, "cfg", "config.json"),
    MCPAUTOCAD_CLAUDE_CONFIG: path.join(temporal, "Claude", "claude_desktop_config.json"),
  };
  const proceso = spawn(PYTHON, ["-m", "mcpautocad", "panel", "--sin-navegador"], { cwd: RAIZ, env, stdio: "ignore" });
  for (let i = 0; i < 50; i++) {
    try { if ((await fetch(URL + "api/estado")).ok) return proceso; } catch (e) { /* aún no */ }
    await esperar(200);
  }
  throw new Error("El panel no arrancó");
}

async function pagina(navegador, tema, extra = {}) {
  const contexto = await navegador.newContext({
    viewport: { width: 1000, height: 1180 }, deviceScaleFactor: 2, colorScheme: tema, ...extra,
  });
  const p = await contexto.newPage();
  await p.goto(URL);
  await p.addStyleTag({ content: OCULTAR });
  await p.waitForSelector("#tokens:not(:empty)");
  await esperar(500);
  return { contexto, p };
}

// La interfaz de Windows: el botón «Reiniciar Claude» solo existe allí.
const COMO_EN_WINDOWS = () => { puedeReiniciar = true; if (ultimoEstado) pintarEstado(ultimoEstado); };

async function capturas(navegador) {
  for (const tema of ["light", "dark"]) {
    const nombre = tema === "light" ? "claro" : "oscuro";
    const { contexto, p } = await pagina(navegador, tema);
    await p.evaluate(COMO_EN_WINDOWS);

    // Inicio: conectado con Claude Desktop, con el aviso flotante y el de reinicio.
    if (await p.isVisible("#btn-registrar")) await p.click("#btn-registrar");
    await esperar(900);
    await p.evaluate(() => window.scrollTo(0, 0));
    await p.screenshot({ path: path.join(DESTINO, `panel-${nombre}.png`) });

    // Herramientas: tarjetas de modo con su coste y «Cambios sin guardar».
    await p.click("#tab-herramientas");
    await p.click("label.modo:has(input[value=completo])");
    await esperar(1200);
    await p.screenshot({ path: path.join(DESTINO, `panel-herramientas-${nombre}.png`) });
    await p.click("label.modo:has(input[value=ligero])");
    await esperar(500);

    // Ayuda: diagnóstico terminado.
    await p.click("#tab-ayuda");
    await p.click("#btn-diagnostico");
    await p.waitForSelector("#btn-copiar-diag:not([hidden])", { timeout: 60000 });
    await esperar(400);
    await p.evaluate(() => document.getElementById("avisos").replaceChildren());
    await p.locator("#ayuda .tarjeta").first().screenshot({ path: path.join(DESTINO, `panel-diagnostico-${nombre}.png`) });
    await contexto.close();
  }
}

async function animacion(navegador, temporal) {
  const videos = path.join(temporal, "video");
  const { contexto, p } = await pagina(navegador, "light", {
    viewport: { width: 1000, height: 760 }, deviceScaleFactor: 1,
    recordVideo: { dir: videos, size: { width: 1000, height: 760 } },
  });
  await p.evaluate(COMO_EN_WINDOWS);
  await esperar(1500);
  // Herramientas: el contador cambia con cada modo y aparece «Cambios sin guardar».
  await p.click("#tab-herramientas");
  await esperar(1200);
  for (const modo of ["completo", "busqueda", "ligero"]) {
    await p.click(`label.modo:has(input[value=${modo}])`);
    await esperar(1500);
  }
  await p.click("[data-preset=solo2d]");
  await esperar(1500);
  await p.click("#btn-guardar");
  await esperar(2200);
  // Ayuda: el diagnóstico aparece paso a paso.
  await p.click("#tab-ayuda");
  await esperar(600);
  await p.click("#btn-diagnostico");
  await p.waitForSelector("#btn-copiar-diag:not([hidden])", { timeout: 60000 });
  await esperar(2500);
  const video = await p.video().path();
  await contexto.close();

  const gif = path.join(DESTINO, "panel-demo.gif");
  const paleta = path.join(temporal, "paleta.png");
  const filtro = "fps=8,scale=720:-1:flags=lanczos";
  execFileSync("ffmpeg", ["-y", "-loglevel", "error", "-ss", "1.2", "-i", video, "-vf", `${filtro},palettegen=stats_mode=diff`, paleta]);
  execFileSync("ffmpeg", ["-y", "-loglevel", "error", "-ss", "1.2", "-i", video, "-i", paleta, "-lavfi",
    `${filtro} [x]; [x][1:v] paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle`, gif]);
}

(async () => {
  const temporal = fs.mkdtempSync(path.join(os.tmpdir(), "mcpautocad-capturas-"));
  fs.mkdirSync(DESTINO, { recursive: true });
  const panel = await abrirPanel(temporal);
  const navegador = await chromium.launch();
  try {
    await capturas(navegador);
    await animacion(navegador, temporal);
  } finally {
    await navegador.close();
    panel.kill();
    fs.rmSync(temporal, { recursive: true, force: true });
  }
  console.log("Capturas guardadas en", DESTINO);
})();
