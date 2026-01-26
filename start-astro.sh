#!/bin/bash

echo ""
echo "  ========================================"
echo "       🚀 ASTRO - AI Assistant"
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

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "WARNING: Python 3 not found. TUI mode won't be available."
fi

# Install Node dependencies if needed
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

# Install Python dependencies
if command -v pip3 &> /dev/null; then
    if ! pip3 install -q textual rich httpx 2>/dev/null; then
        echo "Warning: Failed to install Python dependencies; TUI may not work."
    fi
fi

echo ""
echo "  How would you like to use ASTRO?"
echo ""
echo "  1) 🌐 Web Interface (opens in browser)"
echo "  2) 💻 Terminal UI (beautiful TUI)"
echo "  3) ⌨️  Classic CLI"
echo ""
read -p "  Choose [1/2/3]: " choice

case $choice in
    1)
        echo ""
        echo "  Starting server and opening browser..."
        npm start &
        sleep 3
        if command -v xdg-open &> /dev/null; then
            xdg-open http://localhost:5000
        elif command -v open &> /dev/null; then
            open http://localhost:5000
        else
            echo "  Open http://localhost:5000 in your browser"
        fi
        wait
        ;;
    2)
        echo ""
        echo "  Starting Terminal UI..."
        npm start &
        sleep 2
        python3 astro.py
        ;;
    3)
        echo ""
        echo "  Starting Classic CLI..."
        npm start &
        sleep 2
        python3 astro.py --cli
        ;;
    *)
        echo ""
        echo "  Starting Web Interface by default..."
        npm start &
        sleep 3
        if command -v xdg-open &> /dev/null; then
            xdg-open http://localhost:5000
        elif command -v open &> /dev/null; then
            open http://localhost:5000
        fi
        wait
        ;;
esac

