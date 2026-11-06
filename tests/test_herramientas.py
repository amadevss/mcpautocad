"""Fase 2: herramientas una por una y prueba de conexión."""

import asyncio
import json
import os
import sys

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

from mcpautocad import catalogo, configuracion, iniciar, probar


def test_desactivadas_se_normalizan():
    cfg = configuracion.normalizar({"desactivadas": ["pid_graph", "PID_GRAPH", " arch_stair ", "system_status",
                                                     "no válido!", 7, "pid_graph"]})
    assert cfg["desactivadas"] == ["arch_stair", "pid_graph"]  # system_status no se puede apagar
    assert configuracion.normalizar({"desactivadas": "a_b, c_d"})["desactivadas"] == ["a_b", "c_d"]
    assert configuracion.normalizar({"desactivadas": None})["desactivadas"] == []


def test_desactivadas_desde_la_extension():
    env = {"MCPAUTOCAD_DESACTIVADAS": "pid_graph, arch_stair"}
    assert configuracion.desde_entorno(env)["desactivadas"] == ["arch_stair", "pid_graph"]
    por_defecto = ["system_run_command", "system_run_lisp"]
    sin_sustituir = {"MCPAUTOCAD_DESACTIVADAS": "${user_config.desactivadas}"}
    assert configuracion.desde_entorno(sin_sustituir)["desactivadas"] == por_defecto
    assert configuracion.desde_entorno({})["desactivadas"] == por_defecto
    assert configuracion.desde_entorno({"MCPAUTOCAD_DESACTIVADAS": ""})["desactivadas"] == []


def test_estimacion_descuenta_las_apagadas():
    base = {"modo": "completo", "desactivadas": []}
    sin = catalogo.estimar(base)
    con = catalogo.estimar({**base, "desactivadas": ["pid_graph", "arch_stair"]})
    tokens = {h["nombre"]: h["tokens"] for h in catalogo.cargar()["herramientas"]}
    assert con["herramientas"] == sin["herramientas"] - 2
    assert con["tokens"] == sin["tokens"] - tokens["pid_graph"] - tokens["arch_stair"]
    # En Búsqueda Claude sigue viendo 3 herramientas, pero puede llegar a menos.
    b = catalogo.estimar({"modo": "busqueda", "desactivadas": ["pid_graph"]})
    assert (b["herramientas"], b["disponibles"]) == (3, 242)


def test_lista_de_herramientas_marca_incluidas_y_activas():
    lista = {h["nombre"]: h for h in catalogo.herramientas({"modo": "ligero", "paquetes": [],
                                                           "desactivadas": ["entity_create_line"]})}
    assert len(lista) == 248
    assert lista["entity_create_line"]["incluida"] and not lista["entity_create_line"]["activa"]
    assert not lista["pid_graph"]["incluida"]  # su paquete está apagado
    assert lista["system_status"]["siempre"]
    assert all(h["descripcion"] for h in lista.values())


def test_quitar_herramientas_ignora_nombres_que_no_existen(capsys):
    class Proveedor:
        def __init__(self):
            self.quitadas = []

        def remove_tool(self, nombre):
            if nombre == "no_existe":
                raise KeyError(nombre)
            self.quitadas.append(nombre)

    class Servidor:
        local_provider = Proveedor()

    assert iniciar.quitar_herramientas(Servidor(), ["pid_graph", "no_existe"]) == ["pid_graph"]
    assert "no_existe" in capsys.readouterr().err


def _servidor(cfg):
    exe = os.environ.get("MCPAUTOCAD_EXE")
    comando, args = (exe, ["servidor"]) if exe else (sys.executable, ["-m", "mcpautocad", "servidor"])
    configuracion.guardar({**cfg, "motor": "ezdxf"})
    return StdioTransport(command=comando, args=args, env={**os.environ, "LOG_LEVEL": "ERROR"})


def test_servidor_no_anuncia_ni_ejecuta_las_apagadas():
    async def probar_servidor():
        async with Client(_servidor({"modo": "ligero", "desactivadas": ["entity_create_line"]})) as c:
            nombres = {h.name for h in await c.list_tools()}
            assert "entity_create_line" not in nombres and "entity_create_circle" in nombres
            assert len(nombres) == 65
        # En modo Búsqueda tampoco se puede llegar a ella a través de call_tool.
        async with Client(_servidor({"modo": "busqueda", "desactivadas": ["entity_create_line"]})) as c:
            encontrado = await c.call_tool("search_tools", {"query": "create line"})
            assert "entity_create_line" not in json.dumps(encontrado.structured_content or {})
            resultado = await c.call_tool("call_tool", {"name": "entity_create_line",
                                                        "arguments": {"x1": 0, "y1": 0, "x2": 1, "y2": 1}},
                                          raise_on_error=False)
            assert resultado.is_error
            # Control: la misma llamada con una herramienta activa sí funciona.
            await c.call_tool("call_tool", {"name": "drawing_new", "arguments": {}})
            bien = await c.call_tool("call_tool", {"name": "entity_create_circle",
                                                   "arguments": {"cx": 0, "cy": 0, "radius": 5}},
                                     raise_on_error=False)
            assert not bien.is_error, bien.content

    asyncio.run(probar_servidor())


def test_probar_conexion_con_ezdxf():
    r = probar.probar({"motor": "ezdxf"})
    assert r["ok"] and r["motor"] == "ezdxf" and "sin AutoCAD" in r["mensaje"]


def test_resumen_de_autocad_real():
    r = probar.resumir({"backend": "com", "connected": True, "autocad_version": "25.0s (LMS Tech)",
                        "active_document": "Dibujo1.dwg", "open_documents": 1})
    assert r["ok"] and "25.0s" in r["mensaje"] and "Dibujo1.dwg" in r["mensaje"]
    r = probar.resumir({"backend": "com", "connected": False, "error": "Cannot connect"})
    assert not r["ok"] and "Abre AutoCAD" in r["mensaje"]
    r = probar.resumir({"backend": "none", "connected": False, "error": "COM backend requested but failed"})
    assert not r["ok"]
