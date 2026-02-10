#!/bin/bash
# Cross-compilation script for Windows .exe using MinGW and Wine
# Run on Linux with: sudo apt install mingw-w64 wine-stable

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_DIR/build/windows"
TEMP_DIR="$BUILD_DIR/temp"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check tools
check_tool() {
    if ! command -v "$1" >/dev/null 2>&1; then
        log_error "$1 is required but not installed"
        return 1
    fi
}

log_info "Checking prerequisites..."
check_tool x86_64-w64-mingw32-g++ || {
    echo "Install with: sudo apt install mingw-w64"
    exit 1
}

# Setup
log_info "Setting up build directory..."
rm -rf "$BUILD_DIR"
mkdir -p "$TEMP_DIR"
mkdir -p "$TEMP_DIR/python"
mkdir -p "$TEMP_DIR/nodejs"
mkdir -p "$TEMP_DIR/bin"

# Build Windows launcher
cat > "$TEMP_DIR/astro-launcher-win.cpp" << 'EOF'
#include <windows.h>
#include <string>
#include <vector>
#include <shlobj.h>
#include <shlwapi.h>

#pragma comment(lib, "shell32.lib")
#pragma comment(lib, "shlwapi.lib")

std::wstring GetAppDir() {
    wchar_t path[MAX_PATH];
    GetModuleFileNameW(NULL, path, MAX_PATH);
    PathRemoveFileSpecW(path);
    return std::wstring(path);
}

void LaunchWebMode(const std::wstring& appDir) {
    std::wstring nodePath = appDir + L"\\nodejs\\node.exe";
    std::wstring serverScript = appDir + L"\\dist\\index.js";
    
    // Start server
    SHELLEXECUTEINFOW sei = { sizeof(sei) };
    sei.fMask = SEE_MASK_NOCLOSEPROCESS;
    sei.lpVerb = L"open";
    sei.lpFile = nodePath.c_str();
    sei.lpParameters = serverScript.c_str();
    sei.lpDirectory = appDir.c_str();
    sei.nShow = SW_HIDE;
    
    if (ShellExecuteExW(&sei)) {
        Sleep(3000);
        ShellExecuteW(NULL, L"open", L"http://localhost:5000", NULL, NULL, SW_SHOWNORMAL);
        
        MessageBoxW(NULL,
            L"ASTRO server is running at http://localhost:5000\n"
            L"Your browser should open automatically.",
            L"ASTRO AI Assistant",
            MB_OK | MB_ICONINFORMATION);
        
        CloseHandle(sei.hProcess);
    }
}

void LaunchTUIMode(const std::wstring& appDir) {
    std::wstring pythonPath = appDir + L"\\python\\python.exe";
    std::wstring astroPy = appDir + L"\\astro.py";
    
    // Start server in background
    SHELLEXECUTEINFOW sei = { sizeof(sei) };
    sei.fMask = SEE_MASK_NOCLOSEPROCESS;
    sei.lpVerb = L"open";
    sei.lpFile = (appDir + L"\\nodejs\\node.exe").c_str();
    sei.lpParameters = (appDir + L"\\dist\\index.js").c_str();
    sei.lpDirectory = appDir.c_str();
    sei.nShow = SW_HIDE;
    ShellExecuteExW(&sei);
    
    Sleep(2000);
    
    // Launch TUI
    ShellExecuteW(NULL, L"open", pythonPath.c_str(), astroPy.c_str(), appDir.c_str(), SW_SHOWNORMAL);
    
    CloseHandle(sei.hProcess);
}

void LaunchCLIMode(const std::wstring& appDir) {
    std::wstring pythonPath = appDir + L"\\python\\python.exe";
    std::wstring params = L"astro.py --cli";
    
    // Start server
    SHELLEXECUTEINFOW sei = { sizeof(sei) };
    sei.fMask = SEE_MASK_NOCLOSEPROCESS;
    sei.lpVerb = L"open";
    sei.lpFile = (appDir + L"\\nodejs\\node.exe").c_str();
    sei.lpParameters = (appDir + L"\\dist\\index.js").c_str();
    sei.lpDirectory = appDir.c_str();
    sei.nShow = SW_HIDE;
    ShellExecuteExW(&sei);
    
    Sleep(2000);
    
    // Launch CLI in new console
    AllocConsole();
    ShellExecuteW(NULL, L"open", pythonPath.c_str(), params.c_str(), appDir.c_str(), SW_SHOWNORMAL);
    
    CloseHandle(sei.hProcess);
}

int WINAPI wWinMain(HINSTANCE, HINSTANCE, LPWSTR lpCmdLine, int) {
    std::wstring appDir = GetAppDir();
    std::wstring cmdLine = lpCmdLine;
    
    // Check for mode
    if (cmdLine.find(L"--mode=web") != std::wstring::npos) {
        LaunchWebMode(appDir);
    } else if (cmdLine.find(L"--mode=tui") != std::wstring::npos) {
        LaunchTUIMode(appDir);
    } else if (cmdLine.find(L"--mode=cli") != std::wstring::npos) {
        LaunchCLIMode(appDir);
    } else {
        int result = MessageBoxW(NULL,
            L"Welcome to ASTRO AI Assistant!\n\n"
            L"Select launch mode:\n\n"
            L"Yes = Web Mode (browser)\n"
            L"No = Terminal UI\n"
            L"Cancel = CLI Mode",
            L"ASTRO AI Assistant",
            MB_YESNOCANCEL | MB_ICONQUESTION);
        
        switch (result) {
            case IDYES: LaunchWebMode(appDir); break;
            case IDNO: LaunchTUIMode(appDir); break;
            case IDCANCEL: LaunchCLIMode(appDir); break;
        }
    }
    
    return 0;
}
EOF

# Compile with MinGW
log_info "Building Windows executable..."
x86_64-w64-mingw32-g++ -o "$TEMP_DIR/bin/astro-launcher.exe" \
    "$TEMP_DIR/astro-launcher-win.cpp" \
    -mwindows \
    -lshlwapi \
    -lshell32 \
    -O2 \
    -static-libgcc \
    -static-libstdc++ \
    2>&1 | head -20

if [ ! -f "$TEMP_DIR/bin/astro-launcher.exe" ]; then
    log_error "Failed to build executable"
    exit 1
fi

log_info "Executable built successfully"

# Download Windows Node.js
NODE_VERSION="20.11.0"
NODE_ZIP="node-v${NODE_VERSION}-win-x64.zip"
NODE_URL="https://nodejs.org/dist/v${NODE_VERSION}/${NODE_ZIP}"

if [ ! -f "$BUILD_DIR/$NODE_ZIP" ]; then
    log_info "Downloading Node.js for Windows..."
    wget -q -O "$BUILD_DIR/$NODE_ZIP" "$NODE_URL" || curl -sL -o "$BUILD_DIR/$NODE_ZIP" "$NODE_URL"
fi

unzip -q "$BUILD_DIR/$NODE_ZIP" -d "$TEMP_DIR"
mkdir -p "$TEMP_DIR/nodejs"
mv "$TEMP_DIR/node-v${NODE_VERSION}-win-x64"/* "$TEMP_DIR/nodejs/"
rmdir "$TEMP_DIR/node-v${NODE_VERSION}-win-x64"

# Download Windows Python embeddable
PYTHON_VERSION="3.11.8"
PYTHON_ZIP="python-${PYTHON_VERSION}-embed-amd64.zip"
PYTHON_URL="https://www.python.org/ftp/python/${PYTHON_VERSION}/${PYTHON_ZIP}"

if [ ! -f "$BUILD_DIR/$PYTHON_ZIP" ]; then
    log_info "Downloading Python for Windows..."
    wget -q -O "$BUILD_DIR/$PYTHON_ZIP" "$PYTHON_URL" || curl -sL -o "$BUILD_DIR/$PYTHON_ZIP" "$PYTHON_URL"
fi

unzip -q "$BUILD_DIR/$PYTHON_ZIP" -d "$TEMP_DIR/python"

# Copy application files
log_info "Copying application files..."
mkdir -p "$TEMP_DIR/dist" "$TEMP_DIR/src" "$TEMP_DIR/web" "$TEMP_DIR/public"

cp -r "$PROJECT_DIR/dist"/* "$TEMP_DIR/dist/" 2>/dev/null || log_warn "No dist/ found"
cp -r "$PROJECT_DIR/src"/* "$TEMP_DIR/src/" 2>/dev/null || true
cp -r "$PROJECT_DIR/web"/* "$TEMP_DIR/web/" 2>/dev/null || true
cp -r "$PROJECT_DIR/public"/* "$TEMP_DIR/public/" 2>/dev/null || true

cp "$PROJECT_DIR/astro.py" "$TEMP_DIR/"
cp "$PROJECT_DIR/astro_shell.py" "$TEMP_DIR/"
cp "$PROJECT_DIR/vibe_shell.py" "$TEMP_DIR/"
cp "$PROJECT_DIR/requirements.txt" "$TEMP_DIR/"
cp "$PROJECT_DIR/package.json" "$TEMP_DIR/"
cp "$PROJECT_DIR/README.md" "$TEMP_DIR/"

# Install npm dependencies (using system's npm, but for Windows modules)
log_info "Installing npm dependencies for Windows..."
(cd "$TEMP_DIR" && npm ci --production --silent 2>&1 | tail -5) || \
    (cd "$TEMP_DIR" && npm install --production --silent 2>&1 | tail -5)

# Create batch file installer as fallback
cat > "$BUILD_DIR/install-astro.bat" << 'BATEOF'
@echo off
setlocal EnableDelayedExpansion

echo ========================================
echo    ASTRO AI Assistant Installer
echo ========================================
echo.

set "INSTALL_DIR=%LOCALAPPDATA%\ASTRO"
set "TEMP_DIR=%TEMP%\astro-install"

echo Installing to: %INSTALL_DIR%

:: Check for Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found. Please install Node.js 18+ from nodejs.org
    pause
    exit /b 1
)

:: Create directories
if exist "%INSTALL_DIR%" rmdir /s /q "%INSTALL_DIR%"
mkdir "%INSTALL_DIR%"
mkdir "%TEMP_DIR%"

:: Extract bundled files
echo Extracting application files...
if exist "%~dp0node_modules" (
    xcopy /s /i "%~dp0node_modules" "%INSTALL_DIR%\node_modules" >nul
)
if exist "%~dp0dist" (
    xcopy /s /i "%~dp0dist" "%INSTALL_DIR%\dist" >nul
)
xcopy /s /i "%~dp0src" "%INSTALL_DIR%\src" >nul 2>&1
xcopy /s /i "%~dp0web" "%INSTALL_DIR%\web" >nul 2>&1
xcopy /s /i "%~dp0public" "%INSTALL_DIR%\public" >nul 2>&1

copy "%~dp0astro.py" "%INSTALL_DIR%\" >nul
copy "%~dp0astro_shell.py" "%INSTALL_DIR%\" >nul
copy "%~dp0vibe_shell.py" "%INSTALL_DIR%\" >nul
copy "%~dp0package.json" "%INSTALL_DIR%\" >nul
copy "%~dp0README.md" "%INSTALL_DIR%\" >nul

:: Install Python dependencies
echo Installing Python dependencies...
python -m pip install -r "%~dp0requirements.txt" --quiet

:: Create launcher
echo Creating launcher...
(
echo @echo off
echo set "ASTRO_DIR=%INSTALL_DIR%"
echo cd /d "%%ASTRO_DIR%%"
echo start /b node "%%ASTRO_DIR%%\dist\index.js"
echo timeout /t 2 /nobreak ^>nul
echo start http://localhost:5000
) > "%USERPROFILE%\Desktop\ASTRO Web.lnk"

:: Create desktop shortcuts
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\ASTRO AI Assistant.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\astro-launcher.exe'; $Shortcut.IconLocation = '%INSTALL_DIR%\astro-icon.ico'; $Shortcut.Save()"

echo.
echo ========================================
echo    Installation Complete!
echo ========================================
echo.
echo Launch ASTRO from your Desktop
echo.
pause
BATEOF

unix2dos "$BUILD_DIR/install-astro.bat" 2>/dev/null || sed -i 's/$/\r/' "$BUILD_DIR/install-astro.bat"

# Try to use Wine with Inno Setup if available
if command -v wine >/dev/null 2>&1; then
    log_info "Wine found, attempting to build with Inno Setup..."
    
    # Check for ISCC.exe in Wine
    if wine cmd /c "if exist %PROGRAMFILES(x86)%\Inno Setup 6\ISCC.exe echo yes" 2>/dev/null | grep -q yes; then
        log_info "Building with Inno Setup..."
        
        # Create ISS file for this build
        cat > "$TEMP_DIR/astro-setup.iss" << ISSOF
[Setup]
AppName=ASTRO AI Assistant
AppVersion=1.0.0-alpha.0
AppPublisher=Senpai-Sama7
AppPublisherURL=https://github.com/Senpai-Sama7/Astro
DefaultDirName={autopf}\ASTRO
DefaultGroupName=ASTRO AI Assistant
OutputDir=$BUILD_DIR
OutputBaseFilename=ASTRO-AI-Assistant-Setup-1.0.0-alpha.0
SetupIconFile=$PROJECT_DIR/public/favicon.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
MinVersion=10.0
UninstallDisplayName=ASTRO AI Assistant
VersionInfoVersion=1.0.0.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create desktop icon"; GroupDescription: "Additional icons:"

[Files]
Source: "$TEMP_DIR\bin\astro-launcher.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "$TEMP_DIR\nodejs\*"; DestDir: "{app}\nodejs"; Flags: ignoreversion recursesubdirs
Source: "$TEMP_DIR\python\*"; DestDir: "{app}\python"; Flags: ignoreversion recursesubdirs
Source: "$TEMP_DIR\dist\*"; DestDir: "{app}\dist"; Flags: ignoreversion recursesubdirs
Source: "$TEMP_DIR\src\*"; DestDir: "{app}\src"; Flags: ignoreversion recursesubdirs
Source: "$TEMP_DIR\node_modules\*"; DestDir: "{app}\node_modules"; Flags: ignoreversion recursesubdirs
Source: "$TEMP_DIR\*.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "$TEMP_DIR\*.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "$TEMP_DIR\*.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "$TEMP_DIR\*.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\ASTRO AI Assistant"; Filename: "{app}\astro-launcher.exe"
Name: "{autodesktop}\ASTRO AI Assistant"; Filename: "{app}\astro-launcher.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\astro-launcher.exe"; Description: "Launch ASTRO"; Flags: nowait postinstall skipifsilent
ISSOF

        wine cmd /c "%PROGRAMFILES(x86)%\Inno Setup 6\ISCC.exe" "$TEMP_DIR/astro-setup.iss" 2>&1 | tail -20
        
        if [ -f "$BUILD_DIR/ASTRO-AI-Assistant-Setup-1.0.0-alpha.0.exe" ]; then
            log_info "Windows installer built successfully!"
            ls -lh "$BUILD_DIR/"*.exe
        fi
    else
        log_warn "Inno Setup not found in Wine"
    fi
else
    log_warn "Wine not found, skipping Inno Setup build"
fi

# Create ZIP distribution
log_info "Creating ZIP distribution..."
cd "$TEMP_DIR"
zip -rq "$BUILD_DIR/ASTRO-AI-Assistant-1.0.0-alpha.0-windows.zip" . -x"*.git*"

log_info "Build complete!"
echo ""
echo "Output files:"
ls -lh "$BUILD_DIR/"*.{exe,zip,bat} 2>/dev/null || ls -lh "$BUILD_DIR/"

echo ""
echo "Distribution methods:"
echo "  1. ZIP file: Users extract and run astro-launcher.exe"
echo "  2. Batch installer: Users run install-astro.bat"
if [ -f "$BUILD_DIR/ASTRO-AI-Assistant-Setup-1.0.0-alpha.0.exe" ]; then
    echo "  3. Inno Setup installer: Professional Windows installer"
fi
