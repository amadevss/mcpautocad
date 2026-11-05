<#
  Construye MCP AutoCAD para Windows.

  Resultado en la carpeta "salida":
    - Instalar-MCP-AutoCAD-<version>.exe   instalador (si Inno Setup está instalado)
    - MCP-AutoCAD-portatil-<version>.zip  carpeta lista para usar, sin instalar

  Uso:  powershell -ExecutionPolicy Bypass -File construir.ps1 [-Version 0.1.0]
  Requisitos: Python 3.11+ en el PATH. Inno Setup 6 opcional (choco install innosetup).
#>
param([string]$Version = "")

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not $Version) {
    $Version = (Select-String -Path pyproject.toml -Pattern '^version = "(.+)"').Matches[0].Groups[1].Value
}
Write-Host "== MCP AutoCAD $Version ==" -ForegroundColor Cyan

Write-Host "1/4 Instalando dependencias..."
python -m pip install --upgrade pip
python -m pip install ".[construir]"
if ($LASTEXITCODE -ne 0) { throw "Falló la instalación de dependencias" }

Write-Host "2/4 Empaquetando con PyInstaller..."
python -m PyInstaller --noconfirm --clean mcpautocad.spec
if ($LASTEXITCODE -ne 0) { throw "Falló PyInstaller" }
$exe = Join-Path $PSScriptRoot "dist\mcpautocad\mcpautocad.exe"

Write-Host "3/4 Comprobando el ejecutable..."
& $exe ayuda
if ($LASTEXITCODE -ne 0) { throw "El ejecutable no arranca" }

Write-Host "4/4 Creando paquetes..."
New-Item -ItemType Directory -Force salida | Out-Null
$zip = "salida\MCP-AutoCAD-portatil-$Version.zip"
if (Test-Path $zip) { Remove-Item $zip }
Compress-Archive -Path dist\mcpautocad\* -DestinationPath $zip

$iscc = (Get-Command iscc.exe -ErrorAction SilentlyContinue).Source
if (-not $iscc) {
    foreach ($ruta in @("${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe", "$env:ProgramFiles\Inno Setup 6\ISCC.exe")) {
        if (Test-Path $ruta) { $iscc = $ruta; break }
    }
}
if ($iscc) {
    & $iscc "/DVersion=$Version" "/Osalida" "instalador\mcpautocad.iss"
    if ($LASTEXITCODE -ne 0) { throw "Falló Inno Setup" }
} else {
    Write-Warning "Inno Setup no está instalado: solo se generó el .zip portátil."
}

Write-Host "Listo. Archivos en la carpeta 'salida':" -ForegroundColor Green
Get-ChildItem salida | ForEach-Object { Write-Host "  $($_.Name)" }
