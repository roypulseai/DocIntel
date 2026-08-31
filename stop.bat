@echo off
chcp 65001 >nul
title DocIntel Stopper
color 0C
echo.
echo  Stopping DocIntel...
echo.

REM -- Kill streamlit process --------------------------------------------
taskkill /F /FI "WINDOWTITLE eq streamlit*" >nul 2>nul
taskkill /F /IM streamlit.exe >nul 2>nul
%SYSTEMROOT%\System32\taskkill /F /IM python.exe /FI "WINDOWTITLE eq *streamlit*" >nul 2>nul

REM -- Kill any process listening on port 8501 ----------------------------
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8501" ^| findstr "LISTENING"') do (
    echo  Killing process %%a (Streamlit on port 8501)
    taskkill /F /PID %%a >nul 2>nul
)

echo.
echo  DocIntel has been stopped.
echo.
pause >nul
