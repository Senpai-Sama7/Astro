# Build script for ASTRO Windows installer
# Run this on Windows with PowerShell

param(
    [switch]$SkipDeps = $false,
    [switch]$SkipBuild = $false
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
$BuildDir = "$ProjectDir\build\windows"
$TempDir = "$BuildDir\temp"

# Colors for output
function Write-Info($msg) { Write-Host "[INFO] $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Error($msg) { Write-Host "[ERROR] $msg" -ForegroundColor Red }

# Create directories
Write-Info "Creating build directories..."
New-Item -ItemType Directory -Force -Path $BuildDir | Out-Null
New-Item -ItemType Directory -Force -Path $TempDir | Out-Null
New-Item -ItemType Directory -Force -Path "$TempDir\python" | Out-Null
New-Item -ItemType Directory -Force -Path "$TempDir\nodejs" | Out-Null
New-Item -ItemType Directory -Force -Path "$TempDir\node_modules" | Out-Null
New-Item -ItemType Directory -Force -Path "$TempDir\python-libs" | Out-Null

# Download and extract Node.js
$NodeVersion = "20.11.0"
$NodeZip = "node-v${NodeVersion}-win-x64.zip"
$NodeUrl = "https://nodejs.org/dist/v${NodeVersion}/${NodeZip}"

if (-not $SkipDeps) {
    if (-not (Test-Path "$BuildDir\$NodeZip")) {
        Write-Info "Downloading Node.js ${NodeVersion}..."
        Invoke-WebRequest -Uri $NodeUrl -OutFile "$BuildDir\$NodeZip"
    }
    
    Write-Info "Extracting Node.js..."
    Expand-Archive -Path "$BuildDir\$NodeZip" -DestinationPath "$TempDir" -Force
    Move-Item -Path "$TempDir\node-v${NodeVersion}-win-x64\*" -Destination "$TempDir\nodejs" -Force
    Remove-Item -Path "$TempDir\node-v${NodeVersion}-win-x64" -Recurse -Force
}

# Download and extract Python (embeddable package)
$PythonVersion = "3.11.8"
$PythonZip = "python-${PythonVersion}-embed-amd64.zip"
$PythonUrl = "https://www.python.org/ftp/python/${PythonVersion}/${PythonZip}"

if (-not $SkipDeps) {
    if (-not (Test-Path "$BuildDir\$PythonZip")) {
        Write-Info "Downloading Python ${PythonVersion}..."
        Invoke-WebRequest -Uri $PythonUrl -OutFile "$BuildDir\$PythonZip"
    }
    
    Write-Info "Extracting Python..."
    Expand-Archive -Path "$BuildDir\$PythonZip" -DestinationPath "$TempDir\python" -Force
    
    # Download get-pip.py
    if (-not (Test-Path "$BuildDir\get-pip.py")) {
        Write-Info "Downloading get-pip.py..."
        Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile "$BuildDir\get-pip.py"
    }
    
    # Install pip
    Write-Info "Installing pip..."
    & "$TempDir\python\python.exe" "$BuildDir\get-pip.py" --no-warn-script-location
    
    # Install Python dependencies
    Write-Info "Installing Python dependencies..."
    $reqFile = "$ProjectDir\requirements.txt"
    & "$TempDir\python\python.exe" -m pip install -r $reqFile --target "$TempDir\python-libs" --quiet
}

# Install npm dependencies
if (-not $SkipBuild) {
    Write-Info "Installing npm dependencies..."
    Push-Location $ProjectDir
    
    # Use bundled node
    $env:PATH = "$TempDir\nodejs;$env:PATH"
    
    # Install production dependencies
    & npm ci --production --silent
    
    # Build the project
    Write-Info "Building ASTRO..."
    & npm run build
    
    Pop-Location
    
    # Copy node_modules
    Write-Info "Copying node_modules..."
    Copy-Item -Path "$ProjectDir\node_modules" -Destination "$TempDir" -Recurse -Force
}

# Build the launcher executable
Write-Info "Building launcher executable..."

# Check for Visual Studio / MSBuild
$MsBuildPath = ""
$VsPaths = @(
    "${env:ProgramFiles}\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe",
    "${env:ProgramFiles}\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\MSBuild.exe",
    "${env:ProgramFiles}\Microsoft Visual Studio\2022\Enterprise\MSBuild\Current\Bin\MSBuild.exe",
    "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2019\Community\MSBuild\Current\Bin\MSBuild.exe",
    "${env:ProgramFiles(x86)}\MSBuild\14.0\Bin\MSBuild.exe"
)

foreach ($path in $VsPaths) {
    if (Test-Path $path) {
        $MsBuildPath = $path
        break
    }
}

if ($MsBuildPath -eq "") {
    Write-Warn "MSBuild not found. Attempting to use clang..."
    
    # Try using clang
    $Clang = Get-Command clang -ErrorAction SilentlyContinue
    if ($Clang) {
        & clang++ -o "$BuildDir\astro-launcher.exe" `
            "$ScriptDir\windows\astro-launcher.cpp" `
            -std=c++17 `
            -mwindows `
            -lshlwapi `
            -lshell32 `
            -O2
    } else {
        Write-Error "No C++ compiler found. Please install Visual Studio or Clang."
        exit 1
    }
} else {
    # Create a simple vcxproj for MSBuild
    $Vcxproj = @"
<?xml version="1.0" encoding="utf-8"?>
<Project DefaultTargets="Build" xmlns="http://schemas.microsoft.com/developer/msbuild/2003">
  <ItemGroup Label="ProjectConfigurations">
    <ProjectConfiguration Include="Release|x64">
      <Configuration>Release</Configuration>
      <Platform>x64</Platform>
    </ProjectConfiguration>
  </ItemGroup>
  <PropertyGroup Label="Globals">
    <ProjectGuid>{7C3C5E8F-9A2B-4D6E-8F1A-3B5C7D9E0F2A}</ProjectGuid>
    <RootNamespace>astrolauncher</RootNamespace>
    <WindowsTargetPlatformVersion>10.0</WindowsTargetPlatformVersion>
  </PropertyGroup>
  <Import Project="`$(VCTargetsPath)\Microsoft.Cpp.Default.props" />
  <PropertyGroup Condition="'`$(Configuration)|`$(Platform)'=='Release|x64'" Label="Configuration">
    <ConfigurationType>Application</ConfigurationType>
    <UseDebugLibraries>false</UseDebugLibraries>
    <PlatformToolset>v143</PlatformToolset>
    <WholeProgramOptimization>true</WholeProgramOptimization>
    <CharacterSet>Unicode</CharacterSet>
  </PropertyGroup>
  <Import Project="`$(VCTargetsPath)\Microsoft.Cpp.props" />
  <ImportGroup Label="ExtensionSettings">
  </ImportGroup>
  <ImportGroup Label="PropertySheets" Condition="'`$(Configuration)|`$(Platform)'=='Release|x64'">
    <Import Project="`$(UserRootDir)\Microsoft.Cpp.`$(Platform).user.props" Condition="exists('`$(UserRootDir)\Microsoft.Cpp.`$(Platform).user.props')" Label="LocalAppDataPlatform" />
  </ImportGroup>
  <PropertyGroup Label="UserMacros" />
  <PropertyGroup Condition="'`$(Configuration)|`$(Platform)'=='Release|x64'">
    <LinkIncremental>false</LinkIncremental>
    <OutDir>$BuildDir\</OutDir>
    <IntDir>$BuildDir\obj\</IntDir>
  </PropertyGroup>
  <ItemDefinitionGroup Condition="'\$(Configuration)|\$(Platform)'=='Release|x64'">
    <ClCompile>
      <WarningLevel>Level3</WarningLevel>
      <FunctionLevelLinking>true</FunctionLevelLinking>
      <IntrinsicFunctions>true</IntrinsicFunctions>
      <SDLCheck>true</SDLCheck>
      <PreprocessorDefinitions>NDEBUG;_WINDOWS;%(PreprocessorDefinitions)</PreprocessorDefinitions>
      <ConformanceMode>true</ConformanceMode>
      <LanguageStandard>stdcpp17</LanguageStandard>
    </ClCompile>
    <Link>
      <SubSystem>Windows</SubSystem>
      <EnableCOMDATFolding>true</EnableCOMDATFolding>
      <OptimizeReferences>true</OptimizeReferences>
      <GenerateDebugInformation>true</GenerateDebugInformation>
      <AdditionalDependencies>shell32.lib;shlwapi.lib;%(AdditionalDependencies)</AdditionalDependencies>
    </Link>
  </ItemDefinitionGroup>
  <ItemGroup>
    <ClCompile Include="$ScriptDir\windows\astro-launcher.cpp" />
  </ItemGroup>
  <Import Project="`$(VCTargetsPath)\Microsoft.Cpp.targets" />
</Project>
"@
    
    $VcxprojPath = "$BuildDir\astro-launcher.vcxproj"
    $Vcxproj | Out-File -FilePath $VcxprojPath -Encoding utf8
    
    & $MsBuildPath $VcxprojPath /p:Configuration=Release /p:Platform=x64 /verbosity:minimal
}

if (-not (Test-Path "$BuildDir\astro-launcher.exe")) {
    Write-Error "Failed to build launcher executable"
    exit 1
}

Write-Info "Launcher built successfully"

# Check for Inno Setup
$InnoSetup = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $InnoSetup)) {
    $InnoSetup = "${env:ProgramFiles}\Inno Setup 6\ISCC.exe"
}

if (-not (Test-Path $InnoSetup)) {
    Write-Error "Inno Setup not found. Please install Inno Setup 6."
    Write-Info "Download from: https://jrsoftware.org/isdl.php"
    exit 1
}

# Build the installer
Write-Info "Building installer with Inno Setup..."
& $InnoSetup "$ScriptDir\windows\astro-setup.iss"

if ($LASTEXITCODE -eq 0) {
    Write-Info "Build completed successfully!"
    Write-Info "Installer: $BuildDir\ASTRO-AI-Assistant-Setup-1.0.0-alpha.0.exe"
    
    # Get file size
    $FileInfo = Get-Item "$BuildDir\ASTRO-AI-Assistant-Setup-1.0.0-alpha.0.exe"
    $SizeMB = [math]::Round($FileInfo.Length / 1MB, 2)
    Write-Info "Size: ${SizeMB} MB"
} else {
    Write-Error "Inno Setup build failed"
    exit 1
}
