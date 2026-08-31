#!/bin/bash
# DocIntel Launcher for macOS (.command)
# Double-click this file to run DocIntel. First run auto-installs everything.

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
    echo "     [1/4] Uh oh - Python is not installed yet."
    echo ""
    echo "     Don't worry! Here's what to do (takes 2 minutes):"
    echo "       1. Open  https://www.python.org/downloads/"
    echo "       2. Click the blue 'Download' button"
    echo "       3. Run the downloaded .pkg file"
    echo "       4. Follow the installer (all default choices are fine)"
    echo ""
    echo "     Then double-click this file again. That's it!"
    echo ""
    read -p "Press Enter to close..."
    exit 1
fi
echo ""

# ------------------------------------------------------------------
# 2. Make sure required packages are installed
# ------------------------------------------------------------------
$PY -c "import streamlit, langchain_groq, langgraph, spacy, sklearn, sentence_transformers, faiss" >/dev/null 2>&1
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
        echo "     Please check your internet connection and try again."
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
echo "     To stop the app later: close this window, or press Ctrl+C."
echo "     (You can leave this window open in the background.)"
echo ""

# Launch the server in the background, then open the browser a few
# seconds later. The Groq API key is entered in the app itself.
$PY -m streamlit run app.py --server.port 8501 &
SERVER_PID=$!

sleep 6
open "http://localhost:8501"

echo ""
echo "     DocIntel is running!"
echo "     The app should now be open in your browser."
echo ""

# Keep this window open; closing it (or Ctrl+C) stops the server.
wait $SERVER_PID
