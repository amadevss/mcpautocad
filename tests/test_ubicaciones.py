"""Dónde guarda Claude Desktop su configuración en Windows (escenarios de un equipo real)."""

import json

from mcpautocad import diagnostico, registrar

FAMILIA = "Claude_pzs8sxrjxfjjc"


def carpetas(tmp_path):
    appdata, local = tmp_path / "Roaming", tmp_path / "Local"
    appdata.mkdir()
    local.mkdir()
    return appdata, local


def test_instalador_clasico(tmp_path):
    appdata, local = carpetas(tmp_path)
    u = registrar.ubicaciones_windows(appdata, local)
    assert u["tipo"] == "clasica"
    assert u["activa"] == appdata / "Claude" / registrar.ARCHIVO


def test_tienda_sin_reubicar(tmp_path):
    appdata, local = carpetas(tmp_path)
    (local / "Packages" / FAMILIA).mkdir(parents=True)
    u = registrar.ubicaciones_windows(appdata, local)
    assert u["tipo"] == "tienda"
    assert u["activa"] == local / "Packages" / FAMILIA / "LocalCache" / "Roaming" / "Claude" / registrar.ARCHIVO


def test_tienda_con_datos_reubicados(tmp_path):
    """El caso del equipo real: la configuración vive en Claude-Data\\<familia en minúsculas>."""
    appdata, local = carpetas(tmp_path)
    (local / "Packages" / FAMILIA).mkdir(parents=True)
    (local / "Claude-Data" / FAMILIA.lower()).mkdir(parents=True)
    (appdata / "Claude").mkdir()
    (appdata / "Claude" / f".user-data-left.{FAMILIA}").write_text("")
    u = registrar.ubicaciones_windows(appdata, local)
    assert u["tipo"] == "reubicada"
    assert u["activa"] == local / "Claude-Data" / FAMILIA.lower() / registrar.ARCHIVO
    # Las demás quedan como candidatas, y los registros se buscan en %LOCALAPPDATA%\Claude\logs.
    assert appdata / "Claude" / registrar.ARCHIVO in u["candidatas"]
    assert u["logs"][0] == local / "Claude" / "logs"


def test_reubicada_prefiere_la_carpeta_del_paquete(tmp_path):
    appdata, local = carpetas(tmp_path)
    (local / "Packages" / FAMILIA).mkdir(parents=True)
    (local / "Claude-Data" / "aaa-otra").mkdir(parents=True)
    (local / "Claude-Data" / FAMILIA.lower()).mkdir(parents=True)
    assert registrar.ubicaciones_windows(appdata, local)["activa"].parent.name == FAMILIA.lower()


def _usar_windows_falso(monkeypatch, tmp_path):
    appdata, local = carpetas(tmp_path)
    monkeypatch.delenv("MCPAUTOCAD_CLAUDE_CONFIG")
    monkeypatch.setattr(registrar, "ubicaciones", lambda: registrar.ubicaciones_windows(appdata, local))
    return appdata, local


def test_registrar_escribe_en_la_reubicada_y_conserva_lo_demas(monkeypatch, tmp_path):
    appdata, local = _usar_windows_falso(monkeypatch, tmp_path)
    (local / "Packages" / FAMILIA).mkdir(parents=True)
    real = local / "Claude-Data" / FAMILIA.lower() / registrar.ARCHIVO
    real.parent.mkdir(parents=True)
    original = {"coworkUserFilesPath": "C:/x", "preferences": {"a": 1},
                "mcpServers": {"otro": {"command": "x", "env": {"TOKEN": "secreto"}}}}
    real.write_text(json.dumps(original), encoding="utf-8")

    destinos = registrar.registrar_en_todas()
    assert destinos[0] == real
    datos = json.loads(real.read_text(encoding="utf-8"))
    assert datos["preferences"] == {"a": 1} and datos["coworkUserFilesPath"] == "C:/x"
    assert datos["mcpServers"]["otro"] == original["mcpServers"]["otro"]
    assert datos["mcpServers"]["autocad"]["args"][-1] == "servidor"
    assert not real.read_bytes().startswith(b"\xef\xbb\xbf")  # UTF-8 sin BOM
    assert json.loads(real.with_name(registrar.COPIA).read_text(encoding="utf-8")) == original


def test_diagnostico_detecta_el_registro_en_una_carpeta_que_claude_ya_no_lee(monkeypatch, tmp_path):
    """Lo que pasó con la v0.1.1: registrado en Packages\\...\\LocalCache, pero Claude lee Claude-Data."""
    appdata, local = _usar_windows_falso(monkeypatch, tmp_path)
    vieja = local / "Packages" / FAMILIA / "LocalCache" / "Roaming" / "Claude" / registrar.ARCHIVO
    registrar.agregar(vieja)
    (local / "Claude-Data" / FAMILIA.lower()).mkdir(parents=True)
    (local / "Claude" / "logs").mkdir(parents=True)
    (local / "Claude" / "logs" / "main.log").write_text("[info] user_data_location: 'relocated_local'\n")

    r = diagnostico.diagnosticar(probar_servidor=False)
    paso = next(p for p in r["pasos"] if p["titulo"] == "MCP AutoCAD registrado en Claude")
    assert paso["estado"] == "error" and "que Claude ya no lee" in paso["detalle"]
    assert "relocated_local" in r["informe"]
    assert "Conectar con Claude Desktop" in r["resumen"]

    registrar.registrar_en_todas()  # «Conectar»: ahora va a la carpeta buena
    r = diagnostico.diagnosticar(probar_servidor=False)
    assert next(p for p in r["pasos"] if p["titulo"] == "MCP AutoCAD registrado en Claude")["estado"] == "ok"
