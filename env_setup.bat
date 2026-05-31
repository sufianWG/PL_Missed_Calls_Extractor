@echo off
setlocal
cd /d %~dp0

echo ==========================================
echo MissedCallsPhonLink - Environment Setup
echo ==========================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo Python was not found. Please install Python 3.10 or newer and add it to PATH.
    pause
    exit /b 1
)

if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo Virtual environment already exists.
)

echo.
echo Upgrading pip...
.venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 (
    echo Failed to upgrade pip.
    pause
    exit /b 1
)

echo.
echo Installing Python dependencies...
.venv\Scripts\pip.exe install -r requirements.txt
if errorlevel 1 (
    echo Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo Setup completed successfully.
echo You can now run start.bat
echo.
pause
