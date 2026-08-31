@echo off
chcp 65001 >nul
title DocIntel Launcher
color 0B
setlocal EnableDelayedExpansion

echo.
echo  ================================================
echo   DocIntel - Document Intelligence Launcher
echo  ================================================
echo.

REM -- Check for Python ------------------------------------------------
where python >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON=python"
    goto :python_found
)
where py >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON=py"
    goto :python_found
)

echo  [ERROR] Python is not installed or not found.
echo.
echo  Follow these steps to install Python:
echo     1. Go to https://www.python.org/downloads/
echo     2. Download Python 3.11 or newer
echo     3. Run the installer
echo     4. IMPORTANT: Tick "Add Python to PATH" before installing
echo     5. Click Install Now
echo.
echo  After installing, run this file again.
echo.
pause
exit /b 1

:python_found
echo  [OK] Python found!
echo.

REM -- Check / install dependencies -------------------------------------
echo  Checking components... This may take a while on first run.

call :check_module "%PYTHON%" streamlit
if not "%ERROR%"=="0" goto :deps_missing

call :check_module "%PYTHON%" langchain_groq
if not "%ERROR%"=="0" goto :deps_missing

call :check_module "%PYTHON%" docintel
if not "%ERROR%"=="0" (
    echo  [OK] Package files present.
    set "ERROR=0"
)

REM -- Check spaCy model ------------------------------------------------
echo  Checking spaCy NER model...
%PYTHON% -c "import spacy; spacy.load('en_core_web_sm')" >nul 2>nul
if not "%errorlevel%"=="0" (
    echo  Downloading spaCy model (one time, ~40 MB)...
    %PYTHON% -m spacy download en_core_web_sm
    if not "!errorlevel!"=="0" (
        echo  [ERROR] Failed to download the spaCy model.
        pause
        exit /b 1
    )
)
echo  [OK] spaCy model ready.
echo.

REM -- Check API key -----------------------------------------------------
if not defined GROQ_API_KEY (
    if not exist ".env" (
        echo  First-time setup: You need a free API key.
        echo  It takes 60 seconds: https://console.groq.com
        echo.
        set /p "USERKEY=  Paste your Groq API key (starts with gsk_): "
        if "!USERKEY!"=="" (
            echo.
            echo  No key entered. You can enter it later in the app.
        ) else (
            (
                echo GROQ_API_KEY=!USERKEY!
                echo GROQ_MODEL=llama-3.3-70b-versatile
            ) > "%~dp0.env"
            echo  [OK] Saved your API key to .env
        )
    )
)

REM -- Launch -------------------------------------------------------------
echo.
echo  Starting DocIntel...
echo  Your browser will open automatically.
echo  To stop, run:  stop.bat  (or close this window for CLI mode)
echo  Keep this window open while using the app.
echo.

cd /d "%~dp0"
start "" "%PYTHON%" -m streamlit run app.py --server.port 8501
if %errorlevel% neq 0 goto :deps_missing

REM -- Open browser after short delay ------------------------------------
ping -n 4 127.0.0.1 >nul
start "" "http://localhost:8501"

echo.
echo  DocIntel is running. Close this window to stop the process.
echo.
pause

exit /b 0

:check_module
%PYTHON% -c "import %~2" >nul 2>nul
if "%errorlevel%"=="0" (
    set "ERROR=0"
) else (
    set "ERROR=1"
)
exit /b 0

:deps_missing
echo.
echo  Requirements missing OR launch failed.
echo  Installing dependencies (may take several minutes on first run)...
echo.
%PYTHON% -m pip install -r "%~dp0requirements.txt"
if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Could not install dependencies.
    echo  Try running manually:
    echo    python -m pip install -r requirements.txt
    echo    python -m spacy download en_core_web_sm
    echo    python -m streamlit run app.py
    echo.
    pause
    exit /b 1
)
echo  [OK] Dependencies installed.
echo  Please run this file again to start DocIntel.
echo.
pause
exit /b 0
