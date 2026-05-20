; Inno Setup Script — Graph Launcher
; Compiler : Inno Setup 6.x  https://jrsoftware.org/isinfo.php

#define AppName      "Graph Launcher"
#define AppVersion   "1.2.6"
#define AppPublisher "Ayka"
#define AppURL       "https://www.ayka.dev"
#define AppExe       "Graph Launcher.exe"

[Setup]
AppId={{B8E3F2A1-4C9D-4E7B-8F2A-3D6C9E1B4F7A}}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
OutputDir=installer_output
OutputBaseFilename=Graph_Launcher_Setup_v{#AppVersion}
SetupIconFile=assets\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#AppExe}
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "french";  MessagesFile: "compiler:Languages\French.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; L'exe contient déjà frontend + assets (PyInstaller --onefile)
Source: "dist\{#AppExe}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}";               Filename: "{app}\{#AppExe}"
Name: "{group}\Désinstaller {#AppName}";  Filename: "{uninstallexe}"
Name: "{userdesktop}\{#AppName}";         Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Nettoie les données utilisateur dans %LOCALAPPDATA%\Graph Launcher\
Type: filesandordirs; Name: "{localappdata}\Graph Launcher"
