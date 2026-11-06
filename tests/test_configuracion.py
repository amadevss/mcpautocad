import json
import os

from mcpautocad import configuracion, iniciar


def test_sin_archivo_usa_valores_por_defecto():
    assert configuracion.cargar() == configuracion.POR_DEFECTO
    assert not configuracion.ruta_config().exists()


def test_guardar_y_cargar():
    cfg = {"modo": "busqueda", "paquetes": ["pid", "mecanica"], "3d": True, "motor": "com"}
    configuracion.guardar(cfg)
    leido = configuracion.cargar()
    assert leido == {"modo": "busqueda", "paquetes": ["mecanica", "pid"], "3d": True, "motor": "com",
                     "desactivadas": ["system_run_command", "system_run_lisp"]}
    assert json.loads(configuracion.ruta_config().read_text(encoding="utf-8")) == leido


def test_valores_invalidos_se_corrigen():
    ruta = configuracion.ruta_config()
    ruta.parent.mkdir(parents=True)
    ruta.write_text(json.dumps({"modo": "turbo", "paquetes": ["inventado", "pid"], "3d": "si", "motor": "x"}))
    assert configuracion.cargar() == {"modo": "ligero", "paquetes": ["pid"], "3d": False, "motor": "com",
                                      "desactivadas": ["system_run_command", "system_run_lisp"]}


def test_comandos_y_lisp_apagados_por_defecto():
    assert configuracion.cargar()["desactivadas"] == ["system_run_command", "system_run_lisp"]
    # Una configuración de antes (sin la clave) también las recibe apagadas.
    assert configuracion.normalizar({"modo": "completo"})["desactivadas"] == ["system_run_command", "system_run_lisp"]
    # Pero si el usuario las enciende (lista vacía), se respeta.
    configuracion.guardar({"desactivadas": []})
    assert configuracion.cargar()["desactivadas"] == []


def test_json_roto_no_rompe_nada():
    ruta = configuracion.ruta_config()
    ruta.parent.mkdir(parents=True)
    ruta.write_text("{esto no es json")
    assert configuracion.cargar() == configuracion.POR_DEFECTO


def test_variables_por_modo():
    v = configuracion.variables_entorno({"modo": "completo", "paquetes": []})
    assert v == {
        "AUTOCAD_MCP_BACKEND": "com",
        "TOOL_PROFILE": "full",
        "DISCOVERY_MODE": "off",
        "TOOL_PACKS": "core",
        "ENABLE_3D": "false",
        "DANGEROUS_COMMANDS_ENABLED": "false",
    }
    v = configuracion.variables_entorno({"modo": "ligero"})
    assert (v["TOOL_PROFILE"], v["DISCOVERY_MODE"]) == ("lean", "off")
    v = configuracion.variables_entorno({"modo": "busqueda"})
    assert (v["TOOL_PROFILE"], v["DISCOVERY_MODE"]) == ("full", "search")


def test_variables_paquetes_y_3d():
    v = configuracion.variables_entorno(
        {"paquetes": ["configuracion", "mecanica", "arquitectura", "pid", "planta"], "3d": True})
    assert v["TOOL_PACKS"] == "core,mech,arch,pid,plant,settings"
    assert v["ENABLE_3D"] == "true"


def test_preparar_entorno_lee_el_archivo_y_la_config_manda(monkeypatch):
    configuracion.guardar({"modo": "busqueda", "paquetes": ["pid"], "motor": "ezdxf"})
    monkeypatch.setenv("TOOL_PROFILE", "lean")
    monkeypatch.setenv("DANGEROUS_COMMANDS_ENABLED", "true")
    v = iniciar.preparar_entorno()
    assert os.environ["TOOL_PROFILE"] == "full"
    assert os.environ["DISCOVERY_MODE"] == "search"
    assert os.environ["TOOL_PACKS"] == "core,pid"
    assert os.environ["AUTOCAD_MCP_BACKEND"] == "ezdxf"
    assert os.environ["DANGEROUS_COMMANDS_ENABLED"] == "false"
    assert v["TOOL_PACKS"] == "core,pid"
