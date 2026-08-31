#!/bin/bash
# DocIntel Stopper for macOS / Linux
# Double-click (macOS) or run (Linux) to stop a running DocIntel instance.

cd "$(dirname "$0")"
echo ""
echo "  Stopping DocIntel..."
echo ""

if command -v python3 >/dev/null 2>&1; then
    python3 docintel/tools/stop_server.py
else
    echo "  Could not find python3. DocIntel may not be installed."
fi

echo ""
echo "  Done. If the app was open, refresh the browser tab."
echo ""
read -p "  Press Enter to close..." x
