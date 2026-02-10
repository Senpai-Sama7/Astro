#!/bin/bash
# ASTRO Application Launcher
# Handles different launch modes

ASTRO_DIR="${ASTRO_HOME:-/opt/astro-ai}"
MODE="$1"
PIDFILE="/tmp/astro-$USER.pid"

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$HOME/.local/share/astro/logs/launcher.log"
}

cleanup() {
    if [ -f "$PIDFILE" ]; then
        rm -f "$PIDFILE"
    fi
}

trap cleanup EXIT

# Save PID
echo $$ > "$PIDFILE"

case "$MODE" in
    --mode=web)
        log_message "Starting ASTRO in web mode..."
        
        # Start the server
        cd "$ASTRO_DIR"
        "$ASTRO_DIR/bin/node" "$ASTRO_DIR/dist/index.js" &
        SERVER_PID=$!
        
        # Wait for server to start
        sleep 3
        
        # Open browser
        if command -v xdg-open > /dev/null 2>&1; then
            xdg-open http://localhost:5000
        elif command -v google-chrome > /dev/null 2>&1; then
            google-chrome http://localhost:5000
        elif command -v firefox > /dev/null 2>&1; then
            firefox http://localhost:5000
        fi
        
        # Wait for server
        wait $SERVER_PID
        ;;
        
    --mode=tui)
        log_message "Starting ASTRO in TUI mode..."
        
        # Start server in background
        cd "$ASTRO_DIR"
        "$ASTRO_DIR/bin/node" "$ASTRO_DIR/dist/index.js" &
        SERVER_PID=$!
        
        sleep 2
        
        # Launch TUI
        "$ASTRO_DIR/bin/python3" "$ASTRO_DIR/astro.py" || true
        
        # Stop server
        kill $SERVER_PID 2>/dev/null || true
        ;;
        
    --mode=cli)
        log_message "Starting ASTRO in CLI mode..."
        
        # Start server in background
        cd "$ASTRO_DIR"
        "$ASTRO_DIR/bin/node" "$ASTRO_DIR/dist/index.js" &
        SERVER_PID=$!
        
        sleep 2
        
        # Launch CLI
        "$ASTRO_DIR/bin/python3" "$ASTRO_DIR/astro.py" --cli || true
        
        # Stop server
        kill $SERVER_PID 2>/dev/null || true
        ;;
        
    *)
        echo "Usage: $0 [--mode=web|--mode=tui|--mode=cli]"
        exit 1
        ;;
esac
