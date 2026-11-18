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
const OCULTAR = "#estado-ruta, footer { display: none !important; }";

const esperar = (ms) => new Promise((r) => setTimeout(r, ms));

async function abrirPanel(temporal) {
  fs.mkdirSync(path.join(temporal, "cfg"), { recursive: true });
  fs.writeFileSync(path.join(temporal, "cfg", "config.json"), JSON.stringify({ motor: "ezdxf" }));
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

async function capturas(navegador) {
  for (const tema of ["light", "dark"]) {
    const nombre = tema === "light" ? "claro" : "oscuro";
    const { contexto, p } = await pagina(navegador, tema);
    // Principal: conectado con Claude Desktop y el aviso de "reinicia" a la vista.
    if (await p.isVisible("#btn-registrar")) await p.click("#btn-registrar");
    await esperar(600);
    await p.evaluate(() => window.scrollTo(0, 0));
    await esperar(300);
    await p.screenshot({ path: path.join(DESTINO, `panel-${nombre}.png`) });

    // Herramientas una por una, con una búsqueda en español.
    await p.click("#det-herr summary");
    await esperar(600);
    await p.fill("#buscar", "capa");
    await esperar(400);
    await p.addStyleTag({ content: ".contador { display: none !important; }" });
    const seccion = p.locator("section:has(#det-herr)");
    await seccion.evaluate((e) => {
      e.querySelector("#lista-herr").style.maxHeight = "430px";
      e.querySelector("#lista-herr").style.overflow = "hidden";
    });
    await seccion.screenshot({ path: path.join(DESTINO, `panel-herramientas-${nombre}.png`) });
    await contexto.close();
  }
}

async function animacion(navegador, temporal) {
  const videos = path.join(temporal, "video");
  const { contexto, p } = await pagina(navegador, "light", {
    viewport: { width: 1000, height: 760 }, deviceScaleFactor: 1,
    recordVideo: { dir: videos, size: { width: 1000, height: 760 } },
  });
  // Ir a la tarjeta de modos y recorrerlos: el contador de abajo cambia.
  await p.evaluate(() => document.querySelector(".modos").scrollIntoView({ block: "start" }));
  await p.evaluate(() => window.scrollBy(0, -24));
  await esperar(1200);
  for (const modo of ["completo", "busqueda", "ligero"]) {
    await p.click(`label.modo:has(input[value=${modo}])`);
    await esperar(1500);
  }
  for (const atajo of ["solo2d", "arquitectura", "todo"]) {
    await p.click(`[data-preset=${atajo}]`);
    await esperar(1300);
  }
  await p.click(`label.modo:has(input[value=ligero])`);
  await esperar(1000);
  await p.click("#btn-guardar");
  await esperar(1800);
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
