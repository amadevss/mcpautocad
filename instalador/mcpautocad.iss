; Instalador de MCP AutoCAD (Inno Setup 6). Lo compila construir.ps1.
; Se instala para el usuario actual, sin pedir permisos de administrador.

#ifndef Version
  #define Version "0.0.0"
#endif

[Setup]
AppId={{6F1E3C2A-7B5D-4E8F-9A1C-2D3B4E5F6A7B}
AppName=MCP AutoCAD
AppVersion={#Version}
AppPublisher=amadevss
AppPublisherURL=https://github.com/amadevss/mcpautocad
DefaultDirName={localappdata}\Programs\MCP AutoCAD
DefaultGroupName=MCP AutoCAD
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputBaseFilename=Instalar-MCP-AutoCAD
LicenseFile=..\LICENSE
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=icono.ico
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
UninstallDisplayName=MCP AutoCAD
UninstallDisplayIcon={app}\MCP AutoCAD.exe

[Languages]
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "escritorio"; Description: "Crear un acceso directo en el escritorio"

[Files]
Source: "..\dist\mcpautocad\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\LICENSE"; DestDir: "{app}"; DestName: "LICENSE.txt"

[InstallDelete]
; Accesos directos de la versión 0.1.0, que abrían el panel con consola.
Type: files; Name: "{group}\Panel MCP AutoCAD.lnk"
Type: files; Name: "{userdesktop}\Panel MCP AutoCAD.lnk"

[Icons]
Name: "{group}\MCP AutoCAD"; Filename: "{app}\MCP AutoCAD.exe"
Name: "{group}\Desinstalar MCP AutoCAD"; Filename: "{uninstallexe}"
Name: "{userdesktop}\MCP AutoCAD"; Filename: "{app}\MCP AutoCAD.exe"; Tasks: escritorio

[Run]
Filename: "{app}\mcpautocad.exe"; Parameters: "registrar"; Flags: runhidden waituntilterminated; StatusMsg: "Conectando con Claude Desktop..."
Filename: "{app}\MCP AutoCAD.exe"; Description: "Abrir MCP AutoCAD"; Flags: postinstall nowait skipifsilent

[UninstallRun]
Filename: "{app}\mcpautocad.exe"; Parameters: "quitar"; Flags: runhidden waituntilterminated; RunOnceId: "QuitarDeClaude"

[Messages]
es.FinishedLabel=MCP AutoCAD quedó instalado y conectado con Claude Desktop.%n%nCierra Claude Desktop por completo (también desde la bandeja del sistema) y vuelve a abrirlo.
