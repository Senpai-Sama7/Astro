#!/bin/bash
# Build .deb package using system Node.js and Python
# This is a lighter version for systems that already have Node and Python installed

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_DIR/build/deb"
STAGING_DIR="$BUILD_DIR/astro-ai-assistant-1.0.0"
DEBIAN_DIR="$STAGING_DIR/DEBIAN"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

# Check prerequisites
log_info "Checking prerequisites..."
command -v node >/dev/null 2>&1 || { echo "Node.js required but not installed"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "Python 3 required but not installed"; exit 1; }
command -v dpkg-deb >/dev/null 2>&1 || { echo "dpkg-deb required but not installed"; exit 1; }

NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    log_warn "Node.js 18+ recommended, found $(node --version)"
fi

# Clean and create structure
log_info "Setting up package structure..."
rm -rf "$BUILD_DIR"
mkdir -p "$DEBIAN_DIR"
mkdir -p "$STAGING_DIR/opt/astro-ai"
mkdir -p "$STAGING_DIR/usr/bin"
mkdir -p "$STAGING_DIR/usr/share/applications"
mkdir -p "$STAGING_DIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$STAGING_DIR/etc/astro"

# Copy control files
cp "$SCRIPT_DIR/debian/control" "$DEBIAN_DIR/"
cp "$SCRIPT_DIR/debian/postinst" "$DEBIAN_DIR/"
cp "$SCRIPT_DIR/debian/prerm" "$DEBIAN_DIR/"
chmod 755 "$DEBIAN_DIR/postinst"
chmod 755 "$DEBIAN_DIR/prerm"

# Copy application files
log_info "Copying application files..."
cd "$PROJECT_DIR"

# Build first if needed
if [ ! -d "dist" ]; then
    log_info "Building application..."
    npm run build
fi

# Copy built app
cp -r dist "$STAGING_DIR/opt/astro-ai/"
cp -r src "$STAGING_DIR/opt/astro-ai/"
cp -r web "$STAGING_DIR/opt/astro-ai/" 2>/dev/null || true
cp -r public "$STAGING_DIR/opt/astro-ai/" 2>/dev/null || true
cp package.json "$STAGING_DIR/opt/astro-ai/"
cp package-lock.json "$STAGING_DIR/opt/astro-ai/" 2>/dev/null || true

# Copy Python files
cp astro.py "$STAGING_DIR/opt/astro-ai/"
cp astro_shell.py "$STAGING_DIR/opt/astro-ai/"
cp vibe_shell.py "$STAGING_DIR/opt/astro-ai/"
cp requirements.txt "$STAGING_DIR/opt/astro-ai/"
cp -r astro_os "$STAGING_DIR/opt/astro-ai/" 2>/dev/null || true
cp -r plugins "$STAGING_DIR/opt/astro-ai/" 2>/dev/null || true

# Copy docs
cp README.md "$STAGING_DIR/opt/astro-ai/"
cp LICENSE "$STAGING_DIR/opt/astro-ai/" 2>/dev/null || true

# Copy desktop entry
cp "$SCRIPT_DIR/debian/astro.desktop" "$STAGING_DIR/usr/share/applications/"

# Create wrapper scripts
log_info "Creating launcher scripts..."

# Main launcher
cat > "$STAGING_DIR/usr/bin/astro-desktop" << 'LAUNCHER_EOF'
#!/bin/bash
# ASTRO Desktop Launcher

ASTRO_DIR=/opt/astro-ai
CONFIG_DIR=$HOME/.config/astro
LOG_DIR=$HOME/.local/share/astro/logs

mkdir -p "$CONFIG_DIR" "$LOG_DIR"

export ASTRO_HOME="$ASTRO_DIR"
export NODE_ENV=production
export PATH="$ASTRO_DIR/bin:$PATH"

# Use system node and python
MODE="${1:-auto}"

case "$MODE" in
    web)
        cd "$ASTRO_DIR"
        node "$ASTRO_DIR/dist/index.js" &
        SERVER_PID=$!
        sleep 3
        xdg-open http://localhost:5000 2>/dev/null || true
        wait $SERVER_PID
        ;;
    tui)
        cd "$ASTRO_DIR"
        node "$ASTRO_DIR/dist/index.js" &
        SERVER_PID=$!
        sleep 2
        python3 "$ASTRO_DIR/astro.py"
        kill $SERVER_PID 2>/dev/null || true
        ;;
    cli)
        cd "$ASTRO_DIR"
        node "$ASTRO_DIR/dist/index.js" &
        SERVER_PID=$!
        sleep 2
        python3 "$ASTRO_DIR/astro.py" --cli
        kill $SERVER_PID 2>/dev/null || true
        ;;
    shell)
        python3 "$ASTRO_DIR/astro_shell.py"
        ;;
    vibe)
        python3 "$ASTRO_DIR/vibe_shell.py"
        ;;
    *)
        echo "ASTRO AI Assistant Launcher"
        echo "Usage: astro-desktop [web|tui|cli|shell|vibe]"
        echo ""
        echo "  web   - Launch web interface in browser"
        echo "  tui   - Launch terminal UI"
        echo "  cli   - Launch classic CLI"
        echo "  shell - Launch astro_shell.py (local ReAct)"
        echo "  vibe  - Launch vibe_shell.py (LLM-powered)"
        ;;
esac
LAUNCHER_EOF

chmod 755 "$STAGING_DIR/usr/bin/astro-desktop"

# Create symlinks for direct shell access
ln -sf /opt/astro-ai/astro_shell.py "$STAGING_DIR/usr/bin/astro-shell"
ln -sf /opt/astro-ai/vibe_shell.py "$STAGING_DIR/usr/bin/astro-vibe"

# Install Python dependencies to a local directory
log_info "Installing Python dependencies..."
mkdir -p "$STAGING_DIR/opt/astro-ai/python-libs"
pip3 install -r "$PROJECT_DIR/requirements.txt" \
    --target="$STAGING_DIR/opt/astro-ai/python-libs" \
    --quiet 2>&1 | tail -3 || true

# Create __init__.py for python-libs
if [ -d "$STAGING_DIR/opt/astro-ai/python-libs" ]; then
    touch "$STAGING_DIR/opt/astro-ai/python-libs/__init__.py" 2>/dev/null || true
fi

# Create icon placeholder
mkdir -p "$STAGING_DIR/opt/astro-ai/assets"
touch "$STAGING_DIR/opt/astro-ai/assets/astro-icon.png"
cp "$STAGING_DIR/opt/astro-ai/assets/astro-icon.png" "$STAGING_DIR/usr/share/icons/hicolor/256x256/apps/astro.png" 2>/dev/null || true

# Install npm dependencies
log_info "Installing npm dependencies..."
cd "$STAGING_DIR/opt/astro-ai"
npm ci --production --silent 2>&1 | tail -5 || npm install --production --silent 2>&1 | tail -5

# Set permissions
find "$STAGING_DIR/opt/astro-ai" -type f \( -name "*.js" -o -name "*.py" -o -name "*.json" \) -exec chmod a+r {} \;
chmod -R a+r "$STAGING_DIR/opt/astro-ai"
chmod -R a+x "$STAGING_DIR/opt/astro-ai/node_modules/.bin" 2>/dev/null || true

# Calculate installed size
INSTALLED_SIZE=$(du -sk "$STAGING_DIR" | cut -f1)
echo "Installed-Size: $INSTALLED_SIZE" >> "$DEBIAN_DIR/control"

# Build package
log_info "Building .deb package..."
dpkg-deb --build "$STAGING_DIR" "$BUILD_DIR/astro-ai-assistant_1.0.0-alpha.0_amd64.deb"

# Summary
PACKAGE_SIZE=$(du -h "$BUILD_DIR/astro-ai-assistant_1.0.0-alpha.0_amd64.deb" | cut -f1)
log_info "Package built successfully!"
log_info "Location: $BUILD_DIR/astro-ai-assistant_1.0.0-alpha.0_amd64.deb"
log_info "Size: $PACKAGE_SIZE"
log_info "Installed size: ${INSTALLED_SIZE}KB"

echo ""
echo "To install: sudo dpkg -i $BUILD_DIR/astro-ai-assistant_1.0.0-alpha.0_amd64.deb"
echo "To fix deps: sudo apt-get install -f"
echo "To run:     astro-desktop"
