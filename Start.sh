#!/bin/bash
# DocIntel Launcher for Linux
# Run with:  bash Start.sh   (or ./Start.sh if executable)
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
    echo "   Uh oh - Python 3 is not installed."
    echo "   Install it, e.g.   sudo apt install python3 python3-pip"
    echo "   then run this file again."
    read -p "Press Enter to close..."
    exit 1
fi

"$PY" start.py
