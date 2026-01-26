@echo off
echo.
echo  ========================================
echo       Starting ASTRO - Please wait...
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

echo.
echo  ========================================
echo       ASTRO is starting up!
echo  ========================================
echo.
echo  Open your web browser and go to:
echo.
echo       http://localhost:5000
echo.
echo  Press Ctrl+C to stop ASTRO
echo  ========================================
echo.

:: Start the server
call npm start
