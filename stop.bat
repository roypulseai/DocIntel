@echo off
chcp 65001 >nul
title DocIntel Stopper
color 0C
echo.
echo  Stopping DocIntel...
echo.

cd /d "%~dp0"

where python >nul 2>nul
if %errorlevel%==0 (
    python docintel\tools\stop_server.py
    goto :done
)
where py >nul 2>nul
if %errorlevel%==0 (
    py docintel\tools\stop_server.py
    goto :done
)

echo  Could not find Python. DocIntel may not be installed.

:done
echo.
echo  Done. If the app was open, refresh the browser tab.
echo.
pause
