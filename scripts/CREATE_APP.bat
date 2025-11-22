@echo off
REM VerifiMind - One-Click App Generator
REM Simply double-click this file to create an app!

echo.
echo ========================================================================
echo.
echo           VerifiMind - AI Application Generator
echo              Turn Your Idea Into Reality
echo.
echo ========================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ from python.org
    pause
    exit /b 1
)

echo [OK] Python detected
echo.

REM Run VerifiMind Complete System
python verifimind_complete.py

echo.
echo ========================================================================
echo                     Generation Complete!
echo ========================================================================
echo.
pause
