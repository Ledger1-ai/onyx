@echo off
setlocal enabledelayedexpansion

REM Twitter Agent Dashboard Launcher (virtualenv-aware)
REM This script prefers .\.venv\Scripts\python.exe, then .\venv\Scripts\python.exe,
REM and falls back to system Python if neither virtual environment exists.

echo Starting Twitter Agent Dashboard...
echo.

REM Resolve this script's directory (folder that contains run_dashboard.py)
set "SCRIPT_DIR=%~dp0"

REM Change to the script directory so relative paths work regardless of caller location
pushd "%SCRIPT_DIR%" || (
    echo Failed to change directory to "%SCRIPT_DIR%"
    echo Please run this script from a location with access to the project directory.
    exit /b 1
)

REM Prefer project-local virtualenv pythons
if exist ".\.venv\Scripts\python.exe" (
    echo Using virtualenv: .\.venv\Scripts\python.exe
    ".\.venv\Scripts\python.exe" run_dashboard.py
) else if exist ".\venv\Scripts\python.exe" (
    echo Using virtualenv: .\venv\Scripts\python.exe
    ".\venv\Scripts\python.exe" run_dashboard.py
) else (
    echo Using system Python
    python --version >nul 2>&1
    if errorlevel 1 (
        echo Python is not installed or not in PATH
        echo Please install Python 3.8+ or create a virtualenv (.venv or venv) and try again.
        popd
        exit /b 1
    )
    python run_dashboard.py
)

REM Restore original location
popd

endlocal

REM Propagate the Python process exit code
exit /b %ERRORLEVEL%
