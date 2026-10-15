#define MyAppName "LEED Studio"
#define MyAppVersion "0.11.1"
#define MyAppPublisher "LEED Studio contributors"
#define MyAppExeName "LEED Studio.exe"

[Setup]
AppId={{9B3CDB3B-3A8B-4B7A-9D2C-0A1100000001}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\LEED Studio
DefaultGroupName=LEED Studio
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\release
OutputBaseFilename=LEED-Studio-Setup-0.11.1
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile=..\leed_studio\data\leed_studio.ico

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "..\dist\LEED Studio\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\LEED Studio"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\LEED Studio"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch LEED Studio"; Flags: nowait postinstall skipifsilent
