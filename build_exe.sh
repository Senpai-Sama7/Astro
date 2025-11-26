#!/bin/bash
# ASTRO - Build Windows Executable
# Run this script to create ASTRO.exe

set -e

echo "============================================"
echo "  ASTRO - Building Windows Executable"
echo "============================================"

# Activate virtual environment
source venv/bin/activate

# Clean previous builds
rm -rf build dist

# Build with PyInstaller
echo "Building executable..."
pyinstaller astro.spec --clean

echo ""
echo "============================================"
echo "  Build Complete!"
echo "============================================"
echo "  Executable: dist/ASTRO.exe (Windows)"
echo "  or: dist/ASTRO (Linux)"
echo "============================================"
