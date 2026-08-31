#!/bin/bash
# DocIntel Launcher for macOS (.command)
# Double-click this file to run DocIntel. First run auto-installs everything.

set -e
cd "$(dirname "$0")"

BLUE='\033[0;34m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
echo ""
echo "================================================"
echo "  DocIntel - Document Intelligence Launcher"
echo "================================================"
echo ""

# Locate python3
if command -v python3 >/dev/null 2>&1; then
    PY="python3"
else
    echo "${RED}[ERROR] Python 3 is not installed.${NC}"
    echo "Install it from https://www.python.org/downloads/ then run this again."
    read -p "Press Enter to close..."
    exit 1
fi

PYV=$($PY --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
echo "${GREEN}[OK]${NC} Python $PYV found"

# Ensure pip
echo "Checking pip..."
$PY -m pip install --upgrade pip >/dev/null 2>&1 || true

# Ensure requirements installed
echo "Checking required packages..."
$PY -c "import streamlit, langchain_groq, langgraph, spacy, sklearn" >/dev/null 2>&1 || {
    echo "Installing dependencies (may take a few minutes on first run)..."
    $PY -m pip install -r requirements.txt
    echo "${GREEN}[OK]${NC} Dependencies installed"
}

# Ensure spaCy model
echo "Checking spaCy NER model..."
$PY -c "import spacy; spacy.load('en_core_web_sm')" >/dev/null 2>&1 || {
    echo "Downloading spaCy model (one time, ~40 MB)..."
    $PY -m spacy download en_core_web_sm
    echo "${GREEN}[OK]${NC} spaCy model installed"
}

# Ensure API key (first-run prompt)
if [ -z "$GROQ_API_KEY" ] && [ ! -f ".env" ]; then
    echo ""
    echo "${YELLOW}First-time setup: you need a free API key.${NC}"
    echo "It takes 60 seconds at https://console.groq.com"
    read -p "  Paste your Groq API key (starts with gsk_): " K
    if [ -n "$K" ]; then
        printf 'GROQ_API_KEY=%s\nGROQ_MODEL=llama-3.3-70b-versatile\n' "$K" > .env
        echo "${GREEN}[OK]${NC} Saved your API key to .env"
    fi
fi

# Launch
echo ""
echo "Starting DocIntel... your browser will open in a moment."
echo "To stop it: close this window, or press Ctrl+C."
echo ""
source .env 2>/dev/null || true
export GROQ_API_KEY=${GROQ_API_KEY:-}
$PY -m streamlit run app.py --server.port 8501 &

# Wait then open browser
sleep 4
open "http://localhost:8501"

# Keep window open so user can see logs; closing window stops app
wait
