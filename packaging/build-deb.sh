#!/bin/bash
# Build script for ASTRO .deb package

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_DIR/build/deb"
STAGING_DIR="$BUILD_DIR/astro-ai-assistant-1.0.0"
DEBIAN_DIR="$STAGING_DIR/DEBIAN"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Clean previous builds
log_info "Cleaning previous builds..."
rm -rf "$BUILD_DIR"
mkdir -p "$STAGING_DIR"

# Create directory structure
log_info "Creating package structure..."
mkdir -p "$DEBIAN_DIR"
mkdir -p "$STAGING_DIR/opt/astro-ai"
mkdir -p "$STAGING_DIR/usr/bin"
mkdir -p "$STAGING_DIR/usr/share/applications"
mkdir -p "$STAGING_DIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$STAGING_DIR/etc/astro"

# Copy control files
log_info "Copying Debian control files..."
cp "$SCRIPT_DIR/debian/control" "$DEBIAN_DIR/"
cp "$SCRIPT_DIR/debian/postinst" "$DEBIAN_DIR/"
cp "$SCRIPT_DIR/debian/prerm" "$DEBIAN_DIR/"
chmod 755 "$DEBIAN_DIR/postinst"
chmod 755 "$DEBIAN_DIR/prerm"

# Copy desktop entry
cp "$SCRIPT_DIR/debian/astro.desktop" "$STAGING_DIR/usr/share/applications/"

# Copy launcher scripts
cp "$SCRIPT_DIR/debian/astro-desktop" "$STAGING_DIR/usr/bin/"
cp "$SCRIPT_DIR/debian/astro-launcher.sh" "$STAGING_DIR/opt/astro-ai/bin/astro-launcher"
chmod 755 "$STAGING_DIR/usr/bin/astro-desktop"
chmod 755 "$STAGING_DIR/opt/astro-ai/bin/astro-launcher"

# Copy application files
log_info "Copying application files..."
cd "$PROJECT_DIR"

# Copy main application
cp -r dist "$STAGING_DIR/opt/astro-ai/" 2>/dev/null || log_warn "No dist/ directory found. Run 'npm run build' first."
cp -r src "$STAGING_DIR/opt/astro-ai/"
cp package.json "$STAGING_DIR/opt/astro-ai/"
cp package-lock.json "$STAGING_DIR/opt/astro-ai/" 2>/dev/null || true
cp -r web "$STAGING_DIR/opt/astro-ai/" 2>/dev/null || true
cp -r public "$STAGING_DIR/opt/astro-ai/" 2>/dev/null || true

# Copy Python components
cp astro.py "$STAGING_DIR/opt/astro-ai/"
cp astro_shell.py "$STAGING_DIR/opt/astro-ai/"
cp vibe_shell.py "$STAGING_DIR/opt/astro-ai/"
cp requirements.txt "$STAGING_DIR/opt/astro-ai/"
cp -r astro_os "$STAGING_DIR/opt/astro-ai/" 2>/dev/null || true
cp -r plugins "$STAGING_DIR/opt/astro-ai/" 2>/dev/null || true

# Copy documentation
cp README.md "$STAGING_DIR/opt/astro-ai/"
cp LICENSE "$STAGING_DIR/opt/astro-ai/" 2>/dev/null || true

# Create icon placeholder (would normally be a real PNG)
log_info "Creating application icon..."
if [ -f "$PROJECT_DIR/public/favicon.ico" ]; then
    # Convert or copy icon
    cp "$PROJECT_DIR/public/favicon.ico" "$STAGING_DIR/opt/astro-ai/assets/astro-icon.ico"
    # For PNG, we'd need imagemagick, so create a placeholder
    touch "$STAGING_DIR/opt/astro-ai/assets/astro-icon.png"
else
    mkdir -p "$STAGING_DIR/opt/astro-ai/assets"
    touch "$STAGING_DIR/opt/astro-ai/assets/astro-icon.png"
fi

cp "$STAGING_DIR/opt/astro-ai/assets/"* "$STAGING_DIR/usr/share/icons/hicolor/256x256/apps/astro.png" 2>/dev/null || true

# Bundle Node.js
log_info "Bundling Node.js runtime..."
NODE_VERSION="20.11.0"
NODE_ARCH="linux-x64"
NODE_URL="https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-${NODE_ARCH}.tar.xz"
NODE_DIR="$BUILD_DIR/node-v${NODE_VERSION}-${NODE_ARCH}"

if [ ! -f "$BUILD_DIR/node.tar.xz" ]; then
    log_info "Downloading Node.js ${NODE_VERSION}..."
    wget -q -O "$BUILD_DIR/node.tar.xz" "$NODE_URL" || curl -sL -o "$BUILD_DIR/node.tar.xz" "$NODE_URL"
fi

tar -xf "$BUILD_DIR/node.tar.xz" -C "$BUILD_DIR"

# Copy Node.js binaries
mkdir -p "$STAGING_DIR/opt/astro-ai/bin"
cp "$NODE_DIR/bin/node" "$STAGING_DIR/opt/astro-ai/bin/"
cp "$NODE_DIR/bin/npm" "$STAGING_DIR/opt/astro-ai/bin/" 2>/dev/null || true
cp "$NODE_DIR/bin/npx" "$STAGING_DIR/opt/astro-ai/bin/" 2>/dev/null || true

# Copy Node.js libraries
mkdir -p "$STAGING_DIR/opt/astro-ai/lib"
cp -r "$NODE_DIR/lib/"* "$STAGING_DIR/opt/astro-ai/lib/" 2>/dev/null || true

# Install npm dependencies in staging area
log_info "Installing npm dependencies..."
cd "$STAGING_DIR/opt/astro-ai"
"$STAGING_DIR/opt/astro-ai/bin/npm" ci --production --silent 2>&1 | tail -5 || \
    "$STAGING_DIR/opt/astro-ai/bin/npm" install --production --silent 2>&1 | tail -5

# Bundle Python
log_info "Bundling Python runtime..."
PYTHON_VERSION="3.11.8"
PYTHON_URL="https://github.com/indygreg/python-build-standalone/releases/download/20240107/cpython-${PYTHON_VERSION}+20240107-x86_64-unknown-linux-gnu-install_only.tar.gz"
PYTHON_DIR="$BUILD_DIR/python"

if [ ! -f "$BUILD_DIR/python.tar.gz" ]; then
    log_info "Downloading Python ${PYTHON_VERSION}..."
    wget -q -O "$BUILD_DIR/python.tar.gz" "$PYTHON_URL" || curl -sL -o "$BUILD_DIR/python.tar.gz" "$PYTHON_URL"
fi

tar -xzf "$BUILD_DIR/python.tar.gz" -C "$BUILD_DIR"

# Copy Python
mkdir -p "$STAGING_DIR/opt/astro-ai/python"
cp -r "$PYTHON_DIR/"* "$STAGING_DIR/opt/astro-ai/python/"
ln -sf "$STAGING_DIR/opt/astro-ai/python/bin/python3" "$STAGING_DIR/opt/astro-ai/bin/python3"
ln -sf "$STAGING_DIR/opt/astro-ai/python/bin/pip3" "$STAGING_DIR/opt/astro-ai/bin/pip3"

# Install Python dependencies
log_info "Installing Python dependencies..."
"$STAGING_DIR/opt/astro-ai/python/bin/pip3" install \
    --target="$STAGING_DIR/opt/astro-ai/python/lib/python3.11/site-packages" \
    -r "$STAGING_DIR/opt/astro-ai/requirements.txt" \
    --quiet 2>&1 | tail -5

# Set permissions
log_info "Setting permissions..."
find "$STAGING_DIR/opt/astro-ai" -type f -name "*.sh" -exec chmod +x {} \;
chmod -R a+r "$STAGING_DIR/opt/astro-ai"

# Calculate installed size
INSTALLED_SIZE=$(du -sk "$STAGING_DIR" | cut -f1)
echo "Installed-Size: $INSTALLED_SIZE" >> "$DEBIAN_DIR/control"

# Build the package
log_info "Building .deb package..."
dpkg-deb --build "$STAGING_DIR" "$BUILD_DIR/astro-ai-assistant_1.0.0-alpha.0_amd64.deb"

# Get final size
PACKAGE_SIZE=$(du -h "$BUILD_DIR/astro-ai-assistant_1.0.0-alpha.0_amd64.deb" | cut -f1)

log_info "Package built successfully!"
log_info "Location: $BUILD_DIR/astro-ai-assistant_1.0.0-alpha.0_amd64.deb"
log_info "Size: $PACKAGE_SIZE"
log_info "Installed size: ${INSTALLED_SIZE}KB"

# Verify package
log_info "Verifying package..."
dpkg-deb --info "$BUILD_DIR/astro-ai-assistant_1.0.0-alpha.0_amd64.deb"
dpkg-deb --contents "$BUILD_DIR/astro-ai-assistant_1.0.0-alpha.0_amd64.deb" | head -20

echo ""
log_info "To install: sudo dpkg -i $BUILD_DIR/astro-ai-assistant_1.0.0-alpha.0_amd64.deb"
log_info "To fix dependencies: sudo apt-get install -f"
