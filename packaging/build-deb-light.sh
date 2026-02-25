#!/bin/bash
# Build lightweight .deb that references project files
# For a full bundled version, use build-deb.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_DIR/build/deb"
STAGING_DIR="$BUILD_DIR/astro-ai-assistant-1.0.0"
DEBIAN_DIR="$STAGING_DIR/DEBIAN"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }

# Check prerequisites
command -v dpkg-deb >/dev/null 2>&1 || { echo "dpkg-deb required"; exit 1; }

# Setup
log_info "Creating package structure..."
rm -rf "$BUILD_DIR"
mkdir -p "$DEBIAN_DIR"
mkdir -p "$STAGING_DIR/usr/bin"
mkdir -p "$STAGING_DIR/usr/share/applications"
mkdir -p "$STAGING_DIR/usr/share/doc/astro-ai-assistant"
mkdir -p "$STAGING_DIR/etc/astro"

# Copy control files
cat > "$DEBIAN_DIR/control" << 'EOF'
Package: astro-ai-assistant
Version: 1.0.0-alpha.0
Section: utils
Priority: optional
Architecture: all
Depends: nodejs (>= 18.0.0), npm, python3 (>= 3.11), python3-pip
Recommends: python3-aiofiles, python3-aiohttp
Suggests: google-chrome-stable | chromium-browser | firefox
Maintainer: Douglas Mitchell <senpai-sama7@proton.me>
Homepage: https://github.com/Senpai-Sama7/Astro
Description: AI-powered assistant for task automation
 ASTRO (Autonomous System for Task and Resource Orchestration)
 is an AI-powered assistant with natural language command processing,
 multi-layer security, and both sync/async CLI shells.
 .
 This package installs the ASTRO application with launcher scripts.
 Users should run 'astro-install' after installation to set up
 dependencies in their home directory.
EOF

cat > "$DEBIAN_DIR/postinst" << 'EOF'
#!/bin/bash
set -e

case "$1" in
    configure)
        echo "ASTRO AI Assistant installed!"
        echo ""
        echo "Next steps:"
        echo "  1. Run 'astro-install' to set up dependencies"
        echo "  2. Launch with 'astro-desktop' or from Applications menu"
        echo ""
        update-desktop-database /usr/share/applications 2>/dev/null || true
        ;;
esac

#DEBHELPER#
exit 0
EOF

chmod 755 "$DEBIAN_DIR/postinst"

# Create desktop entry
cat > "$STAGING_DIR/usr/share/applications/astro.desktop" << 'EOF'
[Desktop Entry]
Version=1.0
Name=ASTRO AI Assistant
Comment=AI-powered assistant for task automation
Exec=/usr/bin/astro-desktop
Icon=utilities-terminal
Terminal=false
Type=Application
Categories=Utility;Development;System;AI;
Keywords=AI;assistant;automation;chat;cli;shell;
StartupNotify=true
EOF

# Create main launcher
cat > "$STAGING_DIR/usr/bin/astro-desktop" << 'LAUNCHER'
#!/bin/bash
# ASTRO Desktop Launcher

ASTRO_DIR="${ASTRO_DIR:-$HOME/.local/share/astro}"
CONFIG_DIR="$HOME/.config/astro"
LOG_DIR="$HOME/.local/share/astro/logs"

mkdir -p "$CONFIG_DIR" "$LOG_DIR"

# Check if installed
if [ ! -f "$ASTRO_DIR/package.json" ]; then
    echo "ASTRO not found in $ASTRO_DIR"
    echo "Please run 'astro-install' first"
    exit 1
fi

export ASTRO_HOME="$ASTRO_DIR"
export NODE_ENV=production
cd "$ASTRO_DIR"

MODE="${1:-web}"

case "$MODE" in
    web)
        echo "Starting ASTRO in web mode..."
        node "$ASTRO_DIR/dist/index.js" &
        SERVER_PID=$!
        sleep 3
        xdg-open http://localhost:5000 2>/dev/null || echo "Open http://localhost:5000 in your browser"
        wait $SERVER_PID
        ;;
    tui)
        node "$ASTRO_DIR/dist/index.js" &
        SERVER_PID=$!
        sleep 2
        python3 "$ASTRO_DIR/astro.py"
        kill $SERVER_PID 2>/dev/null
        ;;
    cli)
        node "$ASTRO_DIR/dist/index.js" &
        SERVER_PID=$!
        sleep 2
        python3 "$ASTRO_DIR/astro.py" --cli
        kill $SERVER_PID 2>/dev/null
        ;;
    shell)
        python3 "$ASTRO_DIR/astro_shell.py"
        ;;
    vibe)
        python3 "$ASTRO_DIR/vibe_shell.py"
        ;;
    *)
        echo "Usage: astro-desktop [web|tui|cli|shell|vibe]"
        ;;
esac
LAUNCHER

chmod 755 "$STAGING_DIR/usr/bin/astro-desktop"

# Create install script
cat > "$STAGING_DIR/usr/bin/astro-install" << 'INSTALLER'
#!/bin/bash
# ASTRO Installation Script

set -e

ASTRO_DIR="$HOME/.local/share/astro"
REPO_URL="https://github.com/Senpai-Sama7/Astro"

echo "=== ASTRO AI Assistant Setup ==="
echo ""

# Check dependencies
command -v git >/dev/null 2>&1 || { echo "git required. Install with: sudo apt install git"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "Node.js required. Install with: sudo apt install nodejs npm"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "Python 3 required. Install with: sudo apt install python3 python3-pip"; exit 1; }

# Clone or update
if [ -d "$ASTRO_DIR/.git" ]; then
    echo "Updating existing installation..."
    cd "$ASTRO_DIR"
    git pull
else
    echo "Cloning ASTRO repository..."
    mkdir -p "$ASTRO_DIR"
    git clone --depth 1 "$REPO_URL" "$ASTRO_DIR"
fi

# Install dependencies
echo "Installing Node.js dependencies..."
cd "$ASTRO_DIR"
npm ci --production

echo "Building application..."
npm run build

echo "Installing Python dependencies..."
pip3 install --user -r requirements.txt

# Create desktop entry for user
mkdir -p "$HOME/.local/share/applications"
cat > "$HOME/.local/share/applications/astro.desktop" << EOF
[Desktop Entry]
Version=1.0
Name=ASTRO AI Assistant
Comment=AI-powered assistant
Exec=/usr/bin/astro-desktop
Icon=utilities-terminal
Terminal=false
Type=Application
Categories=Utility;Development;
EOF

update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

echo ""
echo "=== Installation Complete ==="
echo "Launch with: astro-desktop"
echo "Or from your applications menu"
INSTALLER

chmod 755 "$STAGING_DIR/usr/bin/astro-install"

# Create shell wrappers
cat > "$STAGING_DIR/usr/bin/astro-shell" << 'EOF'
#!/bin/bash
python3 "$HOME/.local/share/astro/astro_shell.py" "$@"
EOF

cat > "$STAGING_DIR/usr/bin/astro-vibe" << 'EOF'
#!/bin/bash
python3 "$HOME/.local/share/astro/vibe_shell.py" "$@"
EOF

chmod 755 "$STAGING_DIR/usr/bin/astro-shell"
chmod 755 "$STAGING_DIR/usr/bin/astro-vibe"

# Copy documentation
cp "$PROJECT_DIR/README.md" "$STAGING_DIR/usr/share/doc/astro-ai-assistant/"
cp "$PROJECT_DIR/LICENSE" "$STAGING_DIR/usr/share/doc/astro-ai-assistant/" 2>/dev/null || true

# Calculate size
INSTALLED_SIZE=$(du -sk "$STAGING_DIR" | cut -f1)
echo "Installed-Size: $INSTALLED_SIZE" >> "$DEBIAN_DIR/control"

# Build
log_info "Building package..."
dpkg-deb --build "$STAGING_DIR" "$BUILD_DIR/astro-ai-assistant_1.0.0-alpha.0_all.deb"

PACKAGE_SIZE=$(du -h "$BUILD_DIR/astro-ai-assistant_1.0.0-alpha.0_all.deb" | cut -f1)
log_info "Package built: $BUILD_DIR/astro-ai-assistant_1.0.0-alpha.0_all.deb"
log_info "Size: $PACKAGE_SIZE"

echo ""
echo "Install with: sudo dpkg -i $BUILD_DIR/astro-ai-assistant_1.0.0-alpha.0_all.deb"
