@echo off
REM VerifiMind One-Click Launcher for Windows
REM Double-click this file to launch VerifiMind

title VerifiMind - AI Application Generator

REM Change to project directory
cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.11 or higher from python.org
    pause
    exit /b 1
)

REM Check if virtual environment exists
if exist "venv\Scripts\python.exe" (
    echo [INFO] Using virtual environment
    set PYTHON_CMD=venv\Scripts\python.exe
) else if exist ".venv\Scripts\python.exe" (
    echo [INFO] Using virtual environment (.venv)
    set PYTHON_CMD=.venv\Scripts\python.exe
) else (
    echo [INFO] Using system Python
    set PYTHON_CMD=python
)

REM Launch VerifiMind launcher
echo.
echo ========================================
echo  Starting VerifiMind Launcher...
echo ========================================
echo.

%PYTHON_CMD% launch.py

REM Exit
echo.
echo VerifiMind closed.
pause
