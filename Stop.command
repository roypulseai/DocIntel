#!/bin/bash
# DocIntel Stopper for macOS / Linux
# Double-click (macOS) to stop a running DocIntel instance.
# On Linux run with:  bash Stop.sh

cd "$(dirname "$0")"
echo ""
echo "Stopping DocIntel..."
echo ""

python3 docintel/tools/stop_server.py

echo ""
read -p "Press Enter to close..." x
