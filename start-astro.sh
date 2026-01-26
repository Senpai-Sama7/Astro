#!/bin/bash

echo ""
echo "  ========================================"
echo "       Starting ASTRO - Please wait..."
echo "  ========================================"
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js is not installed!"
    echo ""
    echo "Please install Node.js first:"
    echo "  - Mac: brew install node"
    echo "  - Ubuntu/Debian: sudo apt install nodejs npm"
    echo "  - Or download from: https://nodejs.org/"
    echo ""
    exit 1
fi

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies for the first time..."
    echo "This may take a few minutes..."
    echo ""
    npm install
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install dependencies"
        exit 1
    fi
fi

# Build if needed
if [ ! -d "dist" ]; then
    echo "Building ASTRO..."
    npm run build
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to build"
        exit 1
    fi
fi

echo ""
echo "  ========================================"
echo "       ASTRO is starting up!"
echo "  ========================================"
echo ""
echo "  Open your web browser and go to:"
echo ""
echo "       http://localhost:5000"
echo ""
echo "  Press Ctrl+C to stop ASTRO"
echo "  ========================================"
echo ""

# Start the server
npm start
