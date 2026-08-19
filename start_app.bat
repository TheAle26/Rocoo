@echo off
TITLE Shipping Tool Server
color 0B

:: Force UTF-8 for Python's output. Several status messages contain emoji,
:: which raise UnicodeEncodeError under the console's default codepage if
:: output is ever redirected to a file. That would kill a parsing thread.
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

:: NOTE: every failure check below uses "if errorlevel 1" rather than
:: "if %ERRORLEVEL% NEQ 0". Inside a parenthesised block cmd expands
:: %ERRORLEVEL% when it parses the block, i.e. before the command has run,
:: so it would test a stale value.

echo ===================================================
echo        STARTING SHIPPING TOOL SERVER...
echo ===================================================

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed on this PC!
    echo Please install Python and check the box "Add Python to PATH".
    pause
    exit /b 1
)

:: Check if virtual environment exists. If not, build it.
if not exist "venv\" (
    echo.
    echo [FIRST TIME SETUP] Building virtual environment...
    python -m venv venv
    echo [FIRST TIME SETUP] Installing requirements...
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
    call :check_install
) else (
    echo Activating environment...
    call venv\Scripts\activate.bat
)

:: --- Pull the latest code ---
:: A failed pull used to pass unnoticed, leaving the PC running old code
:: forever while looking like it had updated. Now it says so, loudly.
echo.
git --version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Git is not installed, so this PC cannot receive updates.
    echo Tell the IT department. Starting with the current version...
    pause
) else (
    echo Checking for updates...
    git pull origin main
    call :check_pull
)

echo.
echo Updating dependencies...
pip install -r requirements.txt --quiet
if errorlevel 1 echo [WARNING] Some dependencies could not be updated. Starting anyway...

:: Check that this PC has its printers configured before we start.
if not exist "printers.json" (
    echo.
    echo ***************************************************
    echo  [SETUP NEEDED] printers.json does not exist yet.
    echo.
    echo  Copy printers.example.json to printers.json and put
    echo  in the exact names of this PC's two label printers.
    echo  Printing will not work until you do.
    echo ***************************************************
    echo.
    pause
)

echo.
echo Launching Production Server...
echo Please DO NOT close this black window. To stop the app, click "Shut Down" in the browser.
echo.

:: Automatically open the default web browser to the app
:: (must run BEFORE waitress-serve, which blocks until the server stops)
start http://127.0.0.1:5000

:: --- Run the app using Waitress instead of the Flask dev server ---
waitress-serve --port=5000 app:app

pause
exit /b 0


:check_install
if errorlevel 1 (
    echo.
    echo [ERROR] Could not install the requirements. The app cannot start.
    pause
    exit
)
exit /b 0


:check_pull
if errorlevel 1 (
    echo.
    echo ***************************************************
    echo  [WARNING] COULD NOT DOWNLOAD THE LATEST VERSION
    echo.
    echo  This PC is still running the version it had before.
    echo  Read the git message above and tell the IT department.
    echo  The app will still start, using the old version.
    echo ***************************************************
    echo.
    pause
)
exit /b 0
