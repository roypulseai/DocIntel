@echo off
chcp 65001 >nul
title DocIntel Launcher
color 0A
echo.
echo   ================================================================
echo      DocIntel - Document Intelligence
echo      Starting... (first run auto-installs dependencies)
echo   ================================================================
echo.

cd /d "%~dp0"

where python >nul 2>nul
if %errorlevel%==0 (
    python start.py
    goto :done
)
where py >nul 2>nul
if %errorlevel%==0 (
    py start.py
    goto :done
)

echo.
echo     Uh oh - Python is not installed yet.
echo.
echo     Here's what to do (takes 2 minutes):
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

:done
echo.
echo   DocIntel has stopped.
pause
