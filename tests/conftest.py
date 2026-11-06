import pytest


@pytest.fixture(autouse=True)
def rutas_aisladas(tmp_path, monkeypatch):
    """Ningún test toca la configuración real del usuario ni la de Claude Desktop."""
    monkeypatch.setenv("MCPAUTOCAD_CONFIG", str(tmp_path / "mcpautocad" / "config.json"))
    monkeypatch.setenv("MCPAUTOCAD_CLAUDE_CONFIG", str(tmp_path / "Claude" / "claude_desktop_config.json"))
    for nombre in ("AUTOCAD_MCP_BACKEND", "TOOL_PROFILE", "TOOL_PACKS", "DISCOVERY_MODE",
                   "ENABLE_3D", "DANGEROUS_COMMANDS_ENABLED", "MCPAUTOCAD_ORIGEN", "MCPAUTOCAD_MODO",
                   "MCPAUTOCAD_MECANICA", "MCPAUTOCAD_ARQUITECTURA", "MCPAUTOCAD_PID", "MCPAUTOCAD_PLANTA",
                   "MCPAUTOCAD_CONFIGURACION", "MCPAUTOCAD_3D", "MCPAUTOCAD_MOTOR",
                   "MCPAUTOCAD_DESACTIVADAS"):
        monkeypatch.delenv(nombre, raising=False)
    return tmp_path
