@echo off
setlocal enabledelayedexpansion

:: --- SETTINGS ---
set "REQ_FILE=requirements.txt"
set "MAIN_SCRIPT=src\main.py"
set "PY_URL=https://www.python.org/ftp/python/3.11.5/python-3.11.5-amd64.exe"

echo.
echo ===================================================
echo      Ixchel Hidja - Smart Launcher
echo ===================================================
echo.

:: -----------------------------------------------------
:: 1. DETECT PYTHON (The Smart Check)
:: -----------------------------------------------------
:: First, try the standard 'python' command
set "PYTHON_CMD=python"
python --version >nul 2>&1

if %errorlevel% neq 0 (
    :: If that fails, try the Windows 'py' launcher
    py --version >nul 2>&1
    if !errorlevel! equ 0 (
        echo [INFO] Standard 'python' command not found, but 'py' launcher detected.
        echo [INFO] Using 'py' launcher...
        set "PYTHON_CMD=py"
    ) else (
        :: If both fail, THEN we install
        goto :INSTALL_PYTHON
    )
)

goto :CHECK_DEPS

:INSTALL_PYTHON
echo [STATUS] Python not detected.
echo [ACTION] Downloading Python...
curl -o python_installer.exe "%PY_URL%"
if not exist python_installer.exe (
    echo [ERROR] Download failed. Check internet.
    pause
    exit /b
)
echo [ACTION] Installing... (Wait for the window to finish)
python_installer.exe /passive InstallAllUsers=0 PrependPath=1 Include_pip=1
del python_installer.exe
echo [INFO] Restarting launcher...
start "" "%~f0"
exit /b

:: -----------------------------------------------------
:: 2. CHECK & INSTALL DEPENDENCIES
:: -----------------------------------------------------
:CHECK_DEPS
:: We use the detected command (python or py) to check libraries
"%PYTHON_CMD%" -c "import pygame; import numpy" >nul 2>&1
if %errorlevel% neq 0 (
    echo [STATUS] Installing game libraries...
    :: We use -m pip to ensure we install to the correct Python
    "%PYTHON_CMD%" -m pip install -r %REQ_FILE%
)

:: -----------------------------------------------------
:: 3. LAUNCH GAME
:: -----------------------------------------------------
echo [STATUS] Launching game...
echo ===================================================
"%PYTHON_CMD%" %MAIN_SCRIPT%

if %errorlevel% neq 0 pause