# ASTRO Packaging Guide

This directory contains build scripts and configurations for creating native installers for ASTRO AI Assistant.

## 📦 Available Packages

| Platform | Package | Size | Bundled Dependencies |
|----------|---------|------|---------------------|
| Linux | `.deb` | ~8 KB | System Node.js/Python |
| Windows | `.zip` | ~410 KB | Requires manual Node.js install |
| Windows | Setup `.zip` | ~413 KB | With installer batch script |

---

## 🐧 Linux (.deb)

### Prerequisites
```bash
sudo apt install dpkg-dev debhelper build-essential
```

### Build Commands

**Lightweight version** (uses system Node.js/Python):
```bash
./packaging/build-deb-light.sh
```

**Output:** `build/deb/astro-ai-assistant_1.0.0-alpha.0_all.deb`

**Full bundled version** (includes Node.js and Python):
```bash
./packaging/build-deb.sh
```

**Output:** `build/deb/astro-ai-assistant_1.0.0-alpha.0_amd64.deb`

⚠️ **Note:** The full version downloads ~200MB of dependencies and takes 5-10 minutes.

### Installation
```bash
sudo dpkg -i build/deb/astro-ai-assistant_*.deb
sudo apt-get install -f  # Fix dependencies if needed
astro-install            # Set up ASTRO
```

---

## 🪟 Windows

### Prerequisites

**Option 1 - Simple (Current):**
- zip/unzip tools
- No compilation needed

**Option 2 - Full Build (Windows or Wine):**
- Windows: Visual Studio or MinGW
- Linux: `mingw-w64`, `wine-stable`, `inno-setup`

### Build Commands

**Simple ZIP package** (works on Linux):
```bash
./packaging/build-windows-simple.sh
```

**Outputs:**
- `ASTRO-AI-Assistant-1.0.0-alpha.0-Windows.zip` - Portable
- `ASTRO-AI-Assistant-1.0.0-alpha.0-Windows-Setup.zip` - With installer

**Full installer** (requires Windows or Wine with Inno Setup):
```bash
# On Linux with Wine
sudo apt install mingw-w64 wine-stable
./packaging/build-windows-cross.sh

# On Windows (run in PowerShell)
.\packaging\build-windows.ps1
```

**Output:** `ASTRO-AI-Assistant-Setup-1.0.0-alpha.0.exe`

### Installation

**Portable:**
1. Extract ZIP
2. Run `ASTRO.bat`

**Installer:**
1. Extract Setup ZIP
2. Run `Install-ASTRO.bat` as Administrator
3. Launch from Desktop/Start Menu

---

## 📁 Package Structure

### Linux (.deb)
```
/
├── opt/astro-ai/           # Application files
│   ├── dist/               # Built Node.js app
│   ├── src/                # Source code
│   ├── *.py                # Python shells
│   └── ...
├── usr/bin/
│   ├── astro-desktop       # Main launcher
│   ├── astro-install       # Setup script
│   ├── astro-shell         → astro_shell.py
│   └── astro-vibe          → vibe_shell.py
├── usr/share/applications/
│   └── astro.desktop       # Desktop entry
└── etc/astro/
    └── config.env          # Configuration
```

### Windows (.zip)
```
ASTRO/
├── dist/                   # Built Node.js app
├── src/                    # Source code
├── *.py                    # Python shells
├── ASTRO.bat              # Batch launcher
├── ASTRO.ps1              # PowerShell launcher
├── README-Windows.txt     # Windows-specific docs
└── ...
```

---

## 🔨 Creating a New Release

1. **Update version numbers:**
   - `packaging/debian/control`
   - `packaging/build-deb*.sh`
   - `packaging/build-windows*.sh`
   - `packaging/windows/astro-setup.iss`

2. **Build packages:**
   ```bash
   # Linux
   ./packaging/build-deb-light.sh
   
   # Windows
   ./packaging/build-windows-simple.sh
   ```

3. **Test packages:**
   - Install on clean VM
   - Verify all features work
   - Check desktop shortcuts

4. **Create release:**
   ```bash
   cp build/deb/*.deb release/
   cp build/windows/*.zip release/
   cp build/RELEASE_NOTES.md release/
   ```

---

## 📝 Customization

### Adding Desktop Icons

**Linux:**
- Place icon in `packaging/debian/astro-icon.png`
- Update `packaging/debian/astro.desktop`

**Windows:**
- Place icon in `public/favicon.ico`
- Update `packaging/windows/astro-setup.iss`

### Changing Default Port

Edit the launcher scripts:
- Linux: `packaging/debian/astro-desktop`
- Windows: `ASTRO.bat` or `ASTRO.ps1`

### Adding Dependencies

**Linux:**
Update `packaging/debian/control` Depends: line

**Windows:**
Update the prerequisites check in `Install-ASTRO.bat`

---

## 🔒 Code Signing (Recommended for Production)

### Windows
```powershell
# Sign with Authenticode certificate
signtool.exe sign /f certificate.pfx /p password /tr http://timestamp.digicert.com /td sha256 /fd sha256 ASTRO.exe
```

### Linux
Debian packages are automatically validated via GPG when distributed through APT repositories.

---

## 📊 Package Sizes

| Component | Linux | Windows |
|-----------|-------|---------|
| Core app | ~500 KB | ~500 KB |
| node_modules | ~150 MB | ~150 MB |
| Bundled Node.js | ~40 MB | ~30 MB |
| Bundled Python | ~25 MB | ~15 MB |
| **Total (bundled)** | ~215 MB | ~195 MB |
| **Total (light)** | ~8 KB | ~410 KB |

---

## 🐛 Troubleshooting

### Linux Build Fails
```bash
# Check for missing tools
dpkg-deb --version
which wget curl

# Fix permissions
chmod +x packaging/build-deb*.sh
```

### Windows Build Fails
```bash
# Check for zip
which zip unzip

# For full build, install MinGW
sudo apt install mingw-w64
```

### Package Won't Install
```bash
# Check package integrity
dpkg-deb --info package.deb
dpkg-deb --contents package.deb

# Check dependencies
dpkg -I package.deb | grep Depends
```

---

## 📚 Resources

- [Debian Packaging Policy](https://www.debian.org/doc/debian-policy/)
- [Inno Setup Documentation](https://jrsoftware.org/ishelp/)
- [Microsoft Installer Guidelines](https://docs.microsoft.com/en-us/windows/win32/msi/windows-installer-portal)

---

**For support, open an issue on GitHub.**
