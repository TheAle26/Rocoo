@echo off
TITLE Shipping Tool Server
color 0B

echo ===================================================
echo        STARTING SHIPPING TOOL SERVER...
echo ===================================================

:: Check if Python is installed
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed on this PC! 
    echo Please install Python and check the box "Add Python to PATH".
    pause
    exit
)

:: Check if virtual environment exists. If not, build it.
IF NOT EXIST "venv\" (
    echo.
    echo [FIRST TIME SETUP] Building virtual environment...
    python -m venv venv
    echo [FIRST TIME SETUP] Installing requirements...
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) ELSE (
    echo Activating environment...
    call venv\Scripts\activate.bat
)
git pull origin main
echo.
echo Launching Production Server...
echo Please DO NOT close this black window. To stop the app, click "Shut Down" in the browser.
echo.

:: Automatically open the default web browser to the app
start http://127.0.0.1:5000

:: --- NEW: Run the app using Waitress instead of the Flask dev server ---
waitress-serve --port=5000 app:app

pause