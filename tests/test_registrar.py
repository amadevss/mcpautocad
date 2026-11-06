import json

import pytest

from mcpautocad import registrar


def ruta():
    return registrar.rutas_claude()[0]


def test_crea_el_archivo_si_no_existe():
    registrar.agregar(ruta())
    datos = json.loads(ruta().read_text(encoding="utf-8"))
    entrada = datos["mcpServers"]["autocad"]
    assert entrada["args"][-1] == "servidor"
    assert entrada["command"]
    assert registrar.esta_registrado(ruta())


def test_no_borra_otros_servidores_ni_ajustes():
    ruta().parent.mkdir(parents=True)
    original = {
        "globalShortcut": "Ctrl+Space",
        "mcpServers": {"filesystem": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem"]}},
    }
    ruta().write_text(json.dumps(original), encoding="utf-8")

    registrar.agregar(ruta())
    datos = json.loads(ruta().read_text(encoding="utf-8"))
    assert datos["globalShortcut"] == "Ctrl+Space"
    assert datos["mcpServers"]["filesystem"] == original["mcpServers"]["filesystem"]
    assert "autocad" in datos["mcpServers"]
    # Copia de seguridad del archivo anterior.
    assert json.loads(ruta().with_name(ruta().name + ".bak").read_text(encoding="utf-8")) == original

    assert registrar.quitar(ruta()) is True
    assert json.loads(ruta().read_text(encoding="utf-8")) == original
    assert registrar.quitar(ruta()) is False


def test_registrar_dos_veces_no_duplica():
    registrar.agregar(ruta())
    registrar.agregar(ruta())
    assert list(json.loads(ruta().read_text())["mcpServers"]) == ["autocad"]


def test_archivo_vacio_o_con_bom():
    ruta().parent.mkdir(parents=True)
    ruta().write_text("", encoding="utf-8")
    registrar.agregar(ruta())
    ruta().write_text('﻿{"mcpServers": {"otro": {"command": "x"}}}', encoding="utf-8")
    registrar.agregar(ruta())
    assert set(json.loads(ruta().read_text(encoding="utf-8"))["mcpServers"]) == {"otro", "autocad"}


def test_json_invalido_no_se_sobrescribe():
    ruta().parent.mkdir(parents=True)
    ruta().write_text("{roto", encoding="utf-8")
    with pytest.raises(registrar.ConfigInvalida):
        registrar.agregar(ruta())
    assert ruta().read_text(encoding="utf-8") == "{roto"
    assert registrar.main(["registrar"]) == 1


def test_main_registrar_y_quitar(capsys):
    assert registrar.main([]) == 0
    assert "Reinicia Claude Desktop" in capsys.readouterr().out
    assert registrar.esta_registrado(ruta())
    assert registrar.main(["quitar"]) == 0
    assert not registrar.esta_registrado(ruta())
