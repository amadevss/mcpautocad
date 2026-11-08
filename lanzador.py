"""Punto de entrada para PyInstaller (genera mcpautocad.exe)."""

import sys

from mcpautocad.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
