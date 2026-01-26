@echo off
echo.
echo  ========================================
echo       ASTRO - AI Assistant
echo  ========================================
echo.

:: Check if Node.js is installed
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Node.js is not installed!
    echo.
    echo Please download and install Node.js from:
    echo https://nodejs.org/
    echo.
    pause
    exit /b 1
)

:: Install dependencies if needed
if not exist "node_modules" (
    echo Installing dependencies for the first time...
    echo This may take a few minutes...
    echo.
    call npm install
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

:: Build if needed
if not exist "dist" (
    echo Building ASTRO...
    call npm run build
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR: Failed to build
        pause
        exit /b 1
    )
)

:: Install Python dependencies
pip install -q textual rich httpx 2>nul

echo.
echo  How would you like to use ASTRO?
echo.
echo  1) Web Interface (opens in browser)
echo  2) Terminal UI (beautiful TUI)
echo  3) Classic CLI
echo.
set /p choice="  Choose [1/2/3]: "

if "%choice%"=="1" goto web
if "%choice%"=="2" goto tui
if "%choice%"=="3" goto cli
goto web

:web
echo.
echo  Starting server and opening browser...
start /b npm start
timeout /t 3 >nul
start http://localhost:5000
echo.
echo  Press any key to stop ASTRO...
pause >nul
goto end

:tui
echo.
echo  Starting Terminal UI...
start /b npm start
timeout /t 2 >nul
python astro.py
goto end

:cli
echo.
echo  Starting Classic CLI...
start /b npm start
timeout /t 2 >nul
python astro.py --cli
goto end

:end

