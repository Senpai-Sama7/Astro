#!/bin/bash
# Simple Windows packaging - creates ZIP distribution with batch installer
# No compilation required - uses Windows-native scripts

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_DIR/build/windows"
STAGING_DIR="$BUILD_DIR/staging"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

log_info "Creating Windows package..."
rm -rf "$BUILD_DIR"
mkdir -p "$STAGING_DIR"

# Create directory structure
mkdir -p "$STAGING_DIR/dist"
mkdir -p "$STAGING_DIR/src"
mkdir -p "$STAGING_DIR/web"
mkdir -p "$STAGING_DIR/public"
mkdir -p "$STAGING_DIR/bin"

# Copy application files
log_info "Copying application files..."
cp -r "$PROJECT_DIR/dist"/* "$STAGING_DIR/dist/" 2>/dev/null || log_warn "No dist/ - run 'npm run build' first"
cp -r "$PROJECT_DIR/src"/* "$STAGING_DIR/src/" 2>/dev/null || true
cp -r "$PROJECT_DIR/web"/* "$STAGING_DIR/web/" 2>/dev/null || true
cp -r "$PROJECT_DIR/public"/* "$STAGING_DIR/public/" 2>/dev/null || true

cp "$PROJECT_DIR/astro.py" "$STAGING_DIR/"
cp "$PROJECT_DIR/astro_shell.py" "$STAGING_DIR/"
cp "$PROJECT_DIR/vibe_shell.py" "$STAGING_DIR/"
cp "$PROJECT_DIR/requirements.txt" "$STAGING_DIR/"
cp "$PROJECT_DIR/package.json" "$STAGING_DIR/"
cp "$PROJECT_DIR/package-lock.json" "$STAGING_DIR/" 2>/dev/null || true
cp "$PROJECT_DIR/README.md" "$STAGING_DIR/"
cp "$PROJECT_DIR/LICENSE" "$STAGING_DIR/" 2>/dev/null || true

# Copy node_modules (just production dependencies would be better)
if [ -d "$PROJECT_DIR/node_modules" ]; then
    log_info "Copying node_modules (this may take a while)..."
    cp -r "$PROJECT_DIR/node_modules" "$STAGING_DIR/" 2>/dev/null || log_warn "Could not copy node_modules"
fi

# Create Windows batch launcher
cat > "$STAGING_DIR/ASTRO.bat" << 'EOF'
@echo off
setlocal EnableDelayedExpansion

title ASTRO AI Assistant
set "ASTRO_DIR=%~dp0"
cd /d "%ASTRO_DIR%"

echo ========================================
echo    ASTRO AI Assistant Launcher
echo ========================================
echo.

:: Check for Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found.
    echo Please install Node.js 18+ from https://nodejs.org/
    echo.
    pause
    exit /b 1
)

:: Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo WARNING: Python not found. Some features may not work.
    echo Please install Python 3.11+ from https://python.org/
    echo.
)

echo Select launch mode:
echo.
echo  [1] Web Mode ^(opens browser^)
echo  [2] Terminal UI Mode
echo  [3] CLI Mode
echo  [4] Local Shell ^(astro_shell.py^)
echo  [5] LLM Shell ^(vibe_shell.py^)
echo.
set /p choice="Enter choice (1-5): "

echo.

if "%choice%"=="1" goto web
if "%choice%"=="2" goto tui
if "%choice%"=="3" goto cli
if "%choice%"=="4" goto shell
if "%choice%"=="5" goto vibe
goto end

:web
echo Starting ASTRO in Web Mode...
start /b node "%ASTRO_DIR%\dist\index.js" >nul 2>&1
timeout /t 3 /nobreak >nul
start http://localhost:5000
echo.
echo Server running at http://localhost:5000
echo Browser should open automatically.
echo.
echo Press any key to stop the server...
pause >nul
taskkill /f /im node.exe >nul 2>&1
goto end

:tui
echo Starting ASTRO in TUI Mode...
start /b node "%ASTRO_DIR%\dist\index.js" >nul 2>&1
timeout /t 2 /nobreak >nul
python "%ASTRO_DIR%\astro.py"
taskkill /f /im node.exe >nul 2>&1
goto end

:cli
echo Starting ASTRO in CLI Mode...
start /b node "%ASTRO_DIR%\dist\index.js" >nul 2>&1
timeout /t 2 /nobreak >nul
python "%ASTRO_DIR%\astro.py" --cli
taskkill /f /im node.exe >nul 2>&1
goto end

:shell
echo Starting Local ReAct Shell ^(astro_shell.py^)...
python "%ASTRO_DIR%\astro_shell.py"
goto end

:vibe
echo Starting LLM Shell ^(vibe_shell.py^)...
python "%ASTRO_DIR%\vibe_shell.py"
goto end

:end
echo.
echo Thank you for using ASTRO!
timeout /t 2 /nobreak >nul
EOF

unix2dos "$STAGING_DIR/ASTRO.bat" 2>/dev/null || sed -i 's/$/\r/' "$STAGING_DIR/ASTRO.bat"

# Create PowerShell launcher
cat > "$STAGING_DIR/ASTRO.ps1" << 'EOF'
# ASTRO AI Assistant Launcher for PowerShell
param(
    [Parameter()]
    [ValidateSet("web", "tui", "cli", "shell", "vibe")]
    [string]$Mode = ""
)

$ASTRO_DIR = $PSScriptRoot
Set-Location $ASTRO_DIR

function Test-Command($Command) {
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

function Start-AstroWeb {
    Write-Host "Starting ASTRO in Web Mode..." -ForegroundColor Green
    Start-Process -FilePath "node" -ArgumentList "$ASTRO_DIR\dist\index.js" -WindowStyle Hidden
    Start-Sleep -Seconds 3
    Start-Process "http://localhost:5000"
    Write-Host "Server running at http://localhost:5000" -ForegroundColor Cyan
    Write-Host "Press Enter to stop the server..."
    $null = Read-Host
    Stop-Process -Name "node" -Force -ErrorAction SilentlyContinue
}

function Start-AstroTUI {
    Write-Host "Starting ASTRO in TUI Mode..." -ForegroundColor Green
    Start-Process -FilePath "node" -ArgumentList "$ASTRO_DIR\dist\index.js" -WindowStyle Hidden
    Start-Sleep -Seconds 2
    & python "$ASTRO_DIR\astro.py"
    Stop-Process -Name "node" -Force -ErrorAction SilentlyContinue
}

function Start-AstroCLI {
    Write-Host "Starting ASTRO in CLI Mode..." -ForegroundColor Green
    Start-Process -FilePath "node" -ArgumentList "$ASTRO_DIR\dist\index.js" -WindowStyle Hidden
    Start-Sleep -Seconds 2
    & python "$ASTRO_DIR\astro.py" --cli
    Stop-Process -Name "node" -Force -ErrorAction SilentlyContinue
}

function Start-AstroShell {
    Write-Host "Starting Local ReAct Shell..." -ForegroundColor Green
    & python "$ASTRO_DIR\astro_shell.py"
}

function Start-AstroVibe {
    Write-Host "Starting LLM Shell..." -ForegroundColor Green
    & python "$ASTRO_DIR\vibe_shell.py"
}

# Check prerequisites
if (-not (Test-Command "node")) {
    Write-Error "Node.js not found. Please install from https://nodejs.org/"
    exit 1
}

# Show menu if no mode specified
if (-not $Mode) {
    Write-Host @"
========================================
    ASTRO AI Assistant Launcher
========================================

[1] Web Mode (opens browser)
[2] Terminal UI Mode
[3] CLI Mode
[4] Local ReAct Shell
[5] LLM Shell

"@ -ForegroundColor Cyan

    $choice = Read-Host "Enter choice (1-5)"
    switch ($choice) {
        "1" { $Mode = "web" }
        "2" { $Mode = "tui" }
        "3" { $Mode = "cli" }
        "4" { $Mode = "shell" }
        "5" { $Mode = "vibe" }
        default { 
            Write-Error "Invalid choice"
            exit 1
        }
    }
}

# Launch selected mode
switch ($Mode) {
    "web" { Start-AstroWeb }
    "tui" { Start-AstroTUI }
    "cli" { Start-AstroCLI }
    "shell" { Start-AstroShell }
    "vibe" { Start-AstroVibe }
}
EOF

unix2dos "$STAGING_DIR/ASTRO.ps1" 2>/dev/null || sed -i 's/$/\r/' "$STAGING_DIR/ASTRO.ps1"

# Create Windows installer batch script
cat > "$BUILD_DIR/Install-ASTRO.bat" << 'EOF'
@echo off
setlocal EnableDelayedExpansion

title ASTRO AI Assistant Installer

echo ========================================
echo    ASTRO AI Assistant Installer
echo ========================================
echo.
echo This will install ASTRO to your computer.
echo.

:: Check for Node.js
echo Checking for Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Node.js is required but not installed.
    echo.
    echo Please install Node.js 18+ from:
    echo https://nodejs.org/
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%a in ('node --version') do set NODE_VER=%%a
echo Found: %NODE_VER%
echo.

:: Check for Python
echo Checking for Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo WARNING: Python not found. Some features may not work.
    echo Consider installing Python 3.11+ from python.org
    echo.
) else (
    for /f "tokens=*" %%a in ('python --version') do set PY_VER=%%a
    echo Found: %PY_VER%
)

:: Set installation directory
set "INSTALL_DIR=%LOCALAPPDATA%\ASTRO"
set "SOURCE_DIR=%~dp0"

echo.
echo Installation directory: %INSTALL_DIR%
echo.
set /p confirm="Proceed with installation? (Y/N): "
if /i not "%confirm%"=="Y" goto cancelled

echo.
echo Installing...

:: Create directory
if exist "%INSTALL_DIR%" (
    echo Removing previous installation...
    rmdir /s /q "%INSTALL_DIR%"
)
mkdir "%INSTALL_DIR%"

:: Copy files
echo Copying application files...
xcopy /s /i /q "%SOURCE_DIR%\dist" "%INSTALL_DIR%\dist\" >nul 2>&1 || echo Warning: dist not found
xcopy /s /i /q "%SOURCE_DIR%\src" "%INSTALL_DIR%\src\" >nul 2>&1 || echo Warning: src not found
xcopy /s /i /q "%SOURCE_DIR%\web" "%INSTALL_DIR%\web\" >nul 2>&1 || echo Warning: web not found
xcopy /s /i /q "%SOURCE_DIR%\public" "%INSTALL_DIR%\public\" >nul 2>&1 || echo Warning: public not found
xcopy /s /i /q "%SOURCE_DIR%\node_modules" "%INSTALL_DIR%\node_modules\" >nul 2>&1 || echo Warning: node_modules not found

copy /y "%SOURCE_DIR%\*.py" "%INSTALL_DIR%\" >nul 2>&1
copy /y "%SOURCE_DIR%\*.json" "%INSTALL_DIR%\" >nul 2>&1
copy /y "%SOURCE_DIR%\*.txt" "%INSTALL_DIR%\" >nul 2>&1
copy /y "%SOURCE_DIR%\*.md" "%INSTALL_DIR%\" >nul 2>&1
copy /y "%SOURCE_DIR%\ASTRO.bat" "%INSTALL_DIR%\" >nul 2>&1

:: Create desktop shortcut
set "DESKTOP=%USERPROFILE%\Desktop"
set "SHORTCUT=%DESKTOP%\ASTRO AI Assistant.lnk"

powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT%'); $Shortcut.TargetPath = '%INSTALL_DIR%\ASTRO.bat'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.IconLocation = '%INSTALL_DIR%\public\favicon.ico,0'; $Shortcut.Description = 'ASTRO AI Assistant'; $Shortcut.Save()"

:: Create Start Menu shortcut
set "STARTMENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
copy /y "%SHORTCUT%" "%STARTMENU%\" >nul 2>&1

echo.
echo ========================================
echo    Installation Complete!
echo ========================================
echo.
echo ASTRO has been installed to:
echo   %INSTALL_DIR%
echo.
echo Shortcuts created:
echo   - Desktop
echo   - Start Menu
echo.
echo Launch ASTRO from your Desktop or Start Menu.
echo.
pause
goto end

:cancelled
echo.
echo Installation cancelled.
echo.
pause

:end
EOF

unix2dos "$BUILD_DIR/Install-ASTRO.bat" 2>/dev/null || sed -i 's/$/\r/' "$BUILD_DIR/Install-ASTRO.bat"

# Create ZIP package
log_info "Creating ZIP distribution..."
cd "$STAGING_DIR"
zip -rq "$BUILD_DIR/ASTRO-AI-Assistant-1.0.0-alpha.0-Windows.zip" . -x"*.git*" -x"*__pycache__*"

# Create installer ZIP (includes the installer script)
log_info "Creating installer package..."
cd "$BUILD_DIR"
cp "$STAGING_DIR/ASTRO.bat" .
cp "$STAGING_DIR/ASTRO.ps1" .

# Create README for Windows
cat > "$BUILD_DIR/README-Windows.txt" << 'EOF'
ASTRO AI Assistant - Windows Installation
==========================================

QUICK START (Standalone):
1. Extract ASTRO-AI-Assistant-1.0.0-alpha.0-Windows.zip
2. Double-click ASTRO.bat
3. Select your preferred launch mode

INSTALLER METHOD:
1. Extract ASTRO-AI-Assistant-1.0.0-alpha.0-Windows.zip
2. Run Install-ASTRO.bat as Administrator
3. Follow the prompts
4. Launch from Desktop or Start Menu

PREREQUISITES:
- Windows 10 or later (64-bit)
- Node.js 18+ (download from https://nodejs.org/)
- Python 3.11+ (optional, for shell features)

LAUNCH MODES:
- Web: Opens browser interface at http://localhost:5000
- TUI: Terminal-based user interface
- CLI: Classic command-line interface
- Shell: Local ReAct shell (astro_shell.py)
- Vibe: LLM-powered shell (vibe_shell.py)

TROUBLESHOOTING:
- If "node is not recognized", install Node.js first
- If Python features don't work, install Python 3.11+
- Check Windows Defender isn't blocking the application

For more help, visit: https://github.com/Senpai-Sama7/Astro
EOF

unix2dos "$BUILD_DIR/README-Windows.txt" 2>/dev/null || sed -i 's/$/\r/' "$BUILD_DIR/README-Windows.txt"

# Create final package with installer
zip -q "$BUILD_DIR/ASTRO-AI-Assistant-1.0.0-alpha.0-Windows-Setup.zip" \
    README-Windows.txt \
    Install-ASTRO.bat \
    ASTRO-AI-Assistant-1.0.0-alpha.0-Windows.zip

# Summary
log_info "Windows packages created successfully!"
echo ""
echo "Output files:"
ls -lh "$BUILD_DIR/"*.{zip,bat,txt,ps1} 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'

echo ""
echo "Distribution options:"
echo "  1. ZIP Package:       ASTRO-AI-Assistant-1.0.0-alpha.0-Windows.zip"
echo "     (Users extract and run ASTRO.bat directly)"
echo ""
echo "  2. Setup Package:     ASTRO-AI-Assistant-1.0.0-alpha.0-Windows-Setup.zip"
echo "     (Contains installer script + application)"
