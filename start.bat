@echo off
chcp 65001 >nul
title DocIntel Launcher
color 0A
setlocal EnableDelayedExpansion

:: ┌─────────────────────────────────────────────────────────────┐
:: │  DocIntel - Document Intelligence                           │
:: │  One-click launcher for Windows                             │
:: └─────────────────────────────────────────────────────────────┘

echo.
echo   ================================================================
echo      DocIntel - Document Intelligence
echo      Getting everything ready... please wait
echo   ================================================================
echo.

:: ------------------------------------------------------------------
:: 1. Find Python
:: ------------------------------------------------------------------
set "NEED_INSTALL=0"

where python >nul 2>nul
if %errorlevel%==0 (set "PYTHON=python" & goto :py_ok)
where py >nul 2>nul
if %errorlevel%==0 (set "PYTHON=py" & goto :py_ok)

echo     [1/4] Uh oh - Python is not installed yet.
echo.
echo     Don't worry! Here's what to do (takes 2 minutes):
echo       1. Open  https://www.python.org/downloads/
echo       2. Click the yellow "Download" button
echo       3. Run the downloaded file
echo       4. IMPORTANT: tick the box "Add Python to PATH"
echo       5. Click "Install Now", wait for it to finish
echo.
echo     Then double-click this file again. That's it!
echo.
pause
exit /b 1

:py_ok
for /f %%V in ('%PYTHON% -c "import sys;print(sys.version_info[0])" 2^>nul') do set "PYMAJ=%%V"
if "%PYMAJ%"=="3" (
    echo     [1/4] OK - Python found
) else (
    echo     [1/4] OK - Python found
)
echo.

:: ------------------------------------------------------------------
:: 2. Make sure all needed packages are installed
:: ------------------------------------------------------------------
%PYTHON% -c "import streamlit" >nul 2>nul
if %errorlevel%==0 (set "streamlit_ok=1") else (set "streamlit_ok=0")
%PYTHON% -c "import langchain_groq" >nul 2>nul
if %errorlevel%==0 (set "lg_ok=1") else (set "lg_ok=0")
%PYTHON% -c "import sentence_transformers" >nul 2>nul
if %errorlevel%==0 (set "st_ok=1") else (set "st_ok=0")
%PYTHON% -c "import faiss" >nul 2>nul
if %errorlevel%==0 (set "faiss_ok=1") else (set "faiss_ok=0")

if "%streamlit_ok%"=="1" if "%lg_ok%"=="1" if "%st_ok%"=="1" if "%faiss_ok%"=="1" (
    echo     [2/4] OK - Required packages already installed
) else (
    echo     [2/4] Installing required packages...
    echo             This is only needed the first time and may take
    echo             a few minutes. Please be patient.
    echo.
    %PYTHON% -m pip install --quiet -r "%~dp0requirements.txt"
    if errorlevel 1 (
        echo.
        echo     Something went wrong while installing.
        echo     Please check your internet connection and try again.
        echo.
        pause
        exit /b 1
    )
    echo             Done!
)
echo.

:: ------------------------------------------------------------------
:: 3. Make sure the language model for name detection is available
:: ------------------------------------------------------------------
%PYTHON% -c "import spacy; spacy.load('en_core_web_sm')" >nul 2>nul
if %errorlevel%==0 (
    echo     [3/4] OK - Name detection model ready
) else (
    echo     [3/4] Downloading name detection model ^(one time, ~40 MB^)...
    %PYTHON% -m spacy download en_core_web_sm >nul 2>nul
    if errorlevel 1 (
        echo             Could not download the model. Check your
        echo             internet connection and try again.
        pause
        exit /b 1
    )
    echo             Done!
)
echo.

:: ------------------------------------------------------------------
:: 4. Make sure we have an API key (asked once, then remembered)
:: ------------------------------------------------------------------
if "%GROQ_API_KEY%"=="" (
    if not exist "%~dp0.env" (
        echo     [4/4] Almost there! We need your free API key.
        echo.
        echo     This is what makes the AI work. It's free and takes
        echo     about 60 seconds to get:
        echo.
        echo       1. Open  https://console.groq.com  in your browser
        echo       2. Click "Sign up" ^(free, no credit card^)
        echo       3. On the left click "API Keys"
        echo       4. Click "Create API Key", copy what appears
        echo.
        set /p "APIKEY=     Paste it here (starts with gsk_): "
        if not "!APIKEY!"=="" (
            echo GROQ_API_KEY=!APIKEY!> "%~dp0.env"
            echo GROQ_MODEL=openai/gpt-oss-120b>> "%~dp0.env"
            echo.
            echo     Got it! Your key is saved so you won't be asked again.
        ) else (
            echo.
            echo     No problem - you can add it later inside the app.
        )
    ) else (
        echo     [4/4] OK - API key found
    )
) else (
    echo     [4/4] OK - API key found
)
echo.

:: ------------------------------------------------------------------
:: Launch! (streamlit reads .env itself)
:: ------------------------------------------------------------------
echo   ================================================================
echo      All ready! Starting DocIntel now...
echo   ================================================================
echo.
echo     Your web browser will open automatically to the app.
echo     If it does NOT open, type this into any browser:
echo.
echo           ^>^>^>  http://localhost:8501  ^<^<^<
echo.
echo     You will now see the app's log messages here.
echo     To stop the app: just close this window.
echo.

cd /d "%~dp0"

:: Give the server a few seconds to start, then open the browser
:: automatically. We use a tiny PowerShell helper to avoid the fragile
:: cmd quoting that caused a "> unexpected" error and aborted the launch.
start "" powershell -NoProfile -Command "Start-Sleep -Seconds 6; Start-Process 'http://localhost:8501'"

"%PYTHON%" -m streamlit run app.py --server.port 8501

echo.
echo     DocIntel has stopped.
pause
