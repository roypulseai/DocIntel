#!/bin/bash
# DocIntel Launcher for Linux
# Run with:  bash Start.sh   (or ./Start.sh if executable)

cd "$(dirname "$0")"

GREEN=$(printf '\033[0;32m'); YELLOW=$(printf '\033[1;33m'); RED=$(printf '\033[0;31m'); NC=$(printf '\033[0m')

clear

echo ""
echo "================================================================"
echo "   DocIntel - Document Intelligence"
echo "   Getting everything ready... please wait"
echo "================================================================"
echo ""

PY=""

# ------------------------------------------------------------------
# 1. Find Python
# ------------------------------------------------------------------
if command -v python3 >/dev/null 2>&1; then
    PY="python3"
    echo "     [1/4] OK - Python found ($($PY --version 2>&1 | grep -oE '[0-9]+\.[0-9]+'))"
else
    echo "     [1/4] Uh oh - Python 3 is not installed."
    echo "     Install it, e.g.   sudo apt install python3 python3-pip"
    echo "     then run this file again."
    read -p "Press Enter to close..."
    exit 1
fi
echo ""

# ------------------------------------------------------------------
# 2. Make sure required packages are installed
# ------------------------------------------------------------------
$PY -c "import streamlit, langchain_groq, langgraph, spacy, sklearn, sentence_transformers, faiss, pypdf, docx" >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "     [2/4] OK - Required packages already installed"
else
    echo "     [2/4] Installing required packages..."
    echo "             This is only needed the first time and may take"
    echo "             a few minutes. Please be patient."
    $PY -m pip install --upgrade pip >/dev/null 2>&1 || true
    $PY -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo ""
        echo "     Something went wrong while installing."
        read -p "Press Enter to close..."
        exit 1
    fi
    echo "             Done!"
fi
echo ""

# ------------------------------------------------------------------
# 3. Make sure name-detection model is available
# ------------------------------------------------------------------
$PY -c "import spacy; spacy.load('en_core_web_sm')" >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "     [3/4] OK - Name detection model ready"
else
    echo "     [3/4] Downloading name detection model (one time, ~40 MB)..."
    $PY -m spacy download en_core_web_sm >/dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo "             Could not download the model. Check your internet and try again."
        read -p "Press Enter to close..."
        exit 1
    fi
    echo "             Done!"
fi
echo ""

# ------------------------------------------------------------------
# 4. Reminder about the API key (entered in the app, not here)
# ------------------------------------------------------------------
echo "     [4/4] OK - API key will be entered in the app"
echo ""
echo "     You'll paste your free Groq key in the app's sidebar when it"
echo "     opens. It is NOT saved to disk - enter it each session."
echo "     Get a free key at  https://console.groq.com"
echo ""

# ------------------------------------------------------------------
# Launch!
# ------------------------------------------------------------------
echo "================================================================"
echo "   All ready! Starting DocIntel now..."
echo "================================================================"
echo ""
echo "     Your web browser will open automatically to the app."
echo "     If it does NOT open, type this into any browser:"
echo ""
echo "           >>>  http://localhost:8501  <<<"
echo ""
echo "     To stop the app later: press Ctrl+C in this window."
echo ""

# Launch the server in the background, then open the browser a few
# seconds later. The Groq API key is entered in the app itself.
$PY -m streamlit run app.py --server.port 8501 &
SERVER_PID=$!

sleep 6
# Try to open a browser (use whatever is available)
( xdg-open "http://localhost:8501" >/dev/null 2>&1 || \
  google-chrome "http://localhost:8501" >/dev/null 2>&1 || \
  firefox "http://localhost:8501" >/dev/null 2>&1 ) &
true

echo ""
echo "     DocIntel is running!"
echo "     The app should now be open in your browser."
echo ""

# Keep this window open; Ctrl+C stops the server.
wait $SERVER_PID
