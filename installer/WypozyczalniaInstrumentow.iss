#define MyAppName "Wypożyczalnia Instrumentów"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "Wypożyczalnia Instrumentów"
#define MyAppExeName "WypozyczalniaInstrumentow.exe"
#define MyAppId "{A4D1F0E2-7D8C-4F4A-9C6C-6A6E8D8B8D11}"

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL=https://example.com
DefaultDirName={autopf}\\WypozyczalniaInstrumentow
DefaultGroupName={#MyAppName}
OutputDir=..\\release
OutputBaseFilename=WypozyczalniaInstrumentow_Setup_v{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
UninstallDisplayIcon={app}\\{#MyAppExeName}
SetupIconFile=assets\\WypozyczalniaInstrumentow.ico
WizardImageFile=assets\\WypozyczalniaInstrumentow.png
WizardSmallImageFile=assets\\WypozyczalniaInstrumentow.png
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DisableDirPage=no
DisableProgramGroupPage=no
CloseApplications=yes
RestartApplications=no
VersionInfoVersion=2.0.0.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=Wypożyczalnia Instrumentów - system ewidencji i wypożyczeń
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}

[Languages]
Name: "polish"; MessagesFile: "compiler:Languages\\Polish.isl"

[Tasks]
Name: "desktopicon"; Description: "Utwórz skrót na pulpicie"; GroupDescription: "Dodatkowe skróty:"; Flags: unchecked

[Files]
Source: "..\\dist\\WypozyczalniaInstrumentow\\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "assets\\WypozyczalniaInstrumentow.ico"; DestDir: "{app}\\assets"; Flags: ignoreversion

[Dirs]
Name: "{localappdata}\\WypozyczalniaInstrumentow"
Name: "{localappdata}\\WypozyczalniaInstrumentow\\photos"

[Icons]
Name: "{group}\\Wypożyczalnia Instrumentów"; Filename: "{app}\\{#MyAppExeName}"; IconFilename: "{app}\\assets\\WypozyczalniaInstrumentow.ico"
Name: "{autodesktop}\\Wypożyczalnia Instrumentów"; Filename: "{app}\\{#MyAppExeName}"; IconFilename: "{app}\\assets\\WypozyczalniaInstrumentow.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\\{#MyAppExeName}"; Description: "Uruchom Wypożyczalnię Instrumentów"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Dane użytkownika pozostają w %LOCALAPPDATA% i nie są kasowane przez aktualizację ani deinstalację.
