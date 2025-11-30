@echo off
REM Browser.AI Project Launcher for Windows
REM Quick start script that runs the Python launcher

echo ========================================
echo    Browser.AI Project Launcher
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://www.python.org/
    pause
    exit /b 1
)

REM Run the main launcher script
echo Starting Browser.AI...
echo.
python run_project.py %*

REM Keep window open if there was an error
if errorlevel 1 (
    echo.
    echo ERROR: Browser.AI failed to start
    pause
)
