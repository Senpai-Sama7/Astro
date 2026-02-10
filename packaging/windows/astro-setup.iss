; ASTRO AI Assistant Setup Script for Inno Setup
; Builds a professional Windows installer

#define MyAppName "ASTRO AI Assistant"
#define MyAppVersion "1.0.0-alpha.0"
#define MyAppPublisher "Senpai-Sama7"
#define MyAppURL "https://github.com/Senpai-Sama7/Astro"
#define MyAppExeName "astro-launcher.exe"
#define MyAppAssocName MyAppName + " File"
#define MyAppAssocExt ".astro"
#define MyAppAssocKey StringChange(MyAppAssocName, " ", "") + MyAppAssocExt

[Setup]
AppId={{7C3C5E8F-9A2B-4D6E-8F1A-3B5C7D9E0F2A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\ASTRO
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=..\..\LICENSE
OutputDir=..\..\build\windows
OutputBaseFilename=ASTRO-AI-Assistant-Setup-1.0.0-alpha.0
SetupIconFile=..\..\public\favicon.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
MinVersion=10.0.17763
UninstallDisplayIcon={app}\astro-launcher.exe
UninstallDisplayName={#MyAppName}
VersionInfoVersion=1.0.0.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=AI-powered assistant for task automation
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion=1.0.0.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode
Name: "associations"; Description: "Associate .astro files with {#MyAppName}"; GroupDescription: "File associations:"

[Files]
; Main application files
Source: "..\..\dist\*"; DestDir: "{app}\dist"; Flags: ignoreversion recursesubdirs
Source: "..\..\src\*"; DestDir: "{app}\src"; Flags: ignoreversion recursesubdirs
Source: "..\..\web\*"; DestDir: "{app}\web"; Flags: ignoreversion recursesubdirs; Excludes: "node_modules"
Source: "..\..\public\*"; DestDir: "{app}\public"; Flags: ignoreversion recursesubdirs
Source: "..\..\astro.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\astro_shell.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\vibe_shell.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\package.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\package-lock.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion

; Python runtime (bundled)
Source: "{tmp}\python\*"; DestDir: "{app}\python"; Flags: ignoreversion recursesubdirs external

; Node.js runtime (bundled)
Source: "{tmp}\nodejs\*"; DestDir: "{app}\nodejs"; Flags: ignoreversion recursesubdirs external

; npm dependencies
Source: "{tmp}\node_modules\*"; DestDir: "{app}\node_modules"; Flags: ignoreversion recursesubdirs external

; Python dependencies
Source: "{tmp}\python-libs\*"; DestDir: "{app}\python\Lib\site-packages"; Flags: ignoreversion recursesubdirs external

; Launcher executable
Source: "astro-launcher.exe"; DestDir: "{app}"; Flags: ignoreversion

; Icon files
Source: "..\..\public\favicon.ico"; DestDir: "{app}"; DestName: "astro-icon.ico"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{#MyAppName} (Web Mode)"; Filename: "{app}\{#MyAppExeName}"; Parameters: "--mode=web"
Name: "{group}\{#MyAppName} (CLI Mode)"; Filename: "{app}\{#MyAppExeName}"; Parameters: "--mode=cli"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Registry]
; File association
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocExt}"; ValueType: string; ValueName: ""; ValueData: "{#MyAppAssocKey}"; Flags: uninsdeletevalue; Tasks: associations
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}"; ValueType: string; ValueName: ""; ValueData: "{#MyAppAssocName}"; Flags: uninsdeletekey; Tasks: associations
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\astro-icon.ico"; Tasks: associations
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: associations

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
begin
  ; Check Windows version (Windows 10 or later)
  if not IsWindows10OrGreater() then begin
    MsgBox('This application requires Windows 10 or later.', mbError, MB_OK);
    Result := false;
    Exit;
  end;
  
  ; Check for 64-bit Windows
  if not IsWin64() then begin
    MsgBox('This application requires a 64-bit version of Windows.', mbError, MB_OK);
    Result := false;
    Exit;
  end;
  
  Result := true;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    ; Post-installation setup
  end;
end;

[UninstallDelete]
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\temp"
Type: filesandordirs; Name: "{app}\__pycache__"
