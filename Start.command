#!/bin/bash
# DocIntel Launcher for macOS (.command)
# Double-click this file to run DocIntel.
# All the real work (checking Python, installing deps, downloading the spaCy
# model, launching Streamlit) lives in start.py — this file just runs it.
cd "$(dirname "$0")"

PY=""
if command -v python3 >/dev/null 2>&1; then
    PY="python3"
elif command -v python >/dev/null 2>&1; then
    PY="python"
fi

if [ -z "$PY" ]; then
    echo ""
    echo "   DocIntel needs Python 3."
    echo ""
    echo "   Don't worry! Here's what to do (takes 2 minutes):"
    echo "     1. Open  https://www.python.org/downloads/"
    echo "     2. Click the blue 'Download' button"
    echo "     3. Run the downloaded .pkg file"
    echo "     4. Follow the installer (all default choices are fine)"
    echo ""
    echo "   Then double-click this file again. That's it!"
    echo ""
    read -p "Press Enter to close..."
    exit 1
fi

"$PY" start.py
