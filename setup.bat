@echo off
setlocal
TITLE Shipping Tool - Setup
color 0A

:: One-time setup for a new PC. Double-click it and follow the prompts:
::   1. installs Git and Python 3.13 if they are missing (with winget)
::   2. downloads the program into C:\ShippingTool (asks you to sign in to GitHub)
::   3. asks which printer is which and writes printers.json
::   4. puts a "Shipping Tool" shortcut on the desktop
:: Safe to run again: anything already done is skipped, and an existing
:: printers.json is never touched.
::
:: NOTE: every check uses "if errorlevel 1" outside parenthesised blocks.
:: Inside a block cmd expands %ERRORLEVEL% before the command has run.

if not defined SETUP_DIR set "SETUP_DIR=C:\ShippingTool"
if not defined SETUP_REPO set "SETUP_REPO=https://github.com/TheAle26/Rocoo.git"
set "GIT_EXE=C:\Program Files\Git\cmd\git.exe"
set "PY_EXE=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"

echo ===================================================
echo        SHIPPING TOOL - SETUP FOR A NEW PC
echo ===================================================
echo.

:: ---------------------------------------------------------------- winget
winget --version >nul 2>&1
if errorlevel 1 goto no_winget

:: ---------------------------------------------------------------- 1. Git
echo [1/4] Git
if exist "%GIT_EXE%" goto git_ok
git --version >nul 2>&1
if errorlevel 1 goto git_install
set "GIT_EXE=git"
goto git_ok
:git_install
echo       Installing Git...
winget install --id Git.Git -e --source winget --silent --accept-package-agreements --accept-source-agreements
if not exist "%GIT_EXE%" goto git_failed
:git_ok
echo       OK
echo.

:: ---------------------------------------------------------------- 2. Python
:: Any Python from 3.11 to 3.13 runs the program. Otherwise install 3.13.
echo [2/4] Python
set "PYVER="
for /f "tokens=2" %%v in ('python --version 2^>nul') do set "PYVER=%%v"
echo %PYVER%| findstr /r "^3\.1[123]\." >nul
if not errorlevel 1 goto py_ok
echo       Installing Python 3.13...
winget install --id Python.Python.3.13 -e --source winget --accept-package-agreements --accept-source-agreements --override "/quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1"
if not exist "%PY_EXE%" goto py_failed
set "PYVER=3.13 (just installed)"
:py_ok
echo       OK - Python %PYVER%
echo.

:: ---------------------------------------------------------------- 3. Program
echo [3/4] Program
if exist "%SETUP_DIR%\.git" goto repo_update
echo       Downloading into %SETUP_DIR% ...
echo       If a GitHub window opens, sign in with your GitHub account.
"%GIT_EXE%" clone "%SETUP_REPO%" "%SETUP_DIR%"
if errorlevel 1 goto clone_failed
goto repo_ok
:repo_update
echo       Already installed in %SETUP_DIR%. Getting the latest version...
"%GIT_EXE%" -C "%SETUP_DIR%" pull origin main
if errorlevel 1 echo       [WARNING] Could not update. The installed version stays as it is.
:repo_ok
echo       OK
echo.

:: ---------------------------------------------------------------- 4. Printers + shortcut
echo [4/4] Printers and desktop shortcut
if exist "%SETUP_DIR%\printers.json" goto printers_exist
powershell -NoProfile -ExecutionPolicy Bypass -File "%SETUP_DIR%\choose_printers.ps1" -Shoe "%SETUP_SHOE%" -Box "%SETUP_BOX%"
if errorlevel 1 goto printers_manual
goto printers_ok
:printers_exist
echo       printers.json already exists - left exactly as it is.
echo       (To change the printers later, run choose_printers.ps1 in %SETUP_DIR%.)
goto printers_ok
:printers_manual
echo.
echo       Could not choose the printers automatically. Notepad will open:
echo       put the exact printer names between the quotes, save and close it.
copy /y "%SETUP_DIR%\printers.example.json" "%SETUP_DIR%\printers.json" >nul
start "" /wait notepad "%SETUP_DIR%\printers.json"
:printers_ok

powershell -NoProfile -Command "$d = if ($env:SETUP_DESKTOP) { $env:SETUP_DESKTOP } else { [Environment]::GetFolderPath('Desktop') }; $s = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $d 'Shipping Tool.lnk')); $s.TargetPath = '%SETUP_DIR%\start_app.bat'; $s.WorkingDirectory = '%SETUP_DIR%'; $s.Save()"
if errorlevel 1 (
    echo       [WARNING] Could not create the desktop shortcut.
    echo       Open %SETUP_DIR% and double-click start_app.bat instead.
) else (
    echo       Shortcut "Shipping Tool" created on the desktop.
)

echo.
echo ===================================================
echo  DONE.
echo.
echo  Close this window and open "Shipping Tool" on the
echo  desktop. The first start takes a few minutes while
echo  it installs what it needs.
echo ===================================================
echo.
pause
exit /b 0


:: ---------------------------------------------------------------- errors
:no_winget
echo [ERROR] winget is not available on this PC.
echo Update Windows, or install "App Installer" from the Microsoft Store,
echo then run this setup again.
goto fail

:git_failed
echo [ERROR] Git could not be installed. Check the internet connection and
echo run this setup again.
goto fail

:py_failed
echo [ERROR] Python could not be installed. Check the internet connection and
echo run this setup again.
goto fail

:clone_failed
echo.
echo [ERROR] The program could not be downloaded. Usually this means:
echo   - the GitHub invitation from Alejo has not been accepted yet, or
echo   - you did not sign in to GitHub, or there is no internet.
echo Fix that and run this setup again.
goto fail

:fail
echo.
pause
exit /b 1
