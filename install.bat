@echo off
chcp 65001 >nul
echo ==========================================
echo   Olive Young Crawler Setup (with uv)
echo ==========================================

cd /d "%~dp0"

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b
)

:: Install uv if not present
echo [INFO] Checking/Installing uv...
pip install uv

:: Create Virtual Environment using uv
if not exist venv (
    echo [INFO] Creating virtual environment with uv...
    uv venv
)

:: Activate Virtual Environment
call venv\Scripts\activate

:: Install Dependencies using uv
echo [INFO] Installing dependencies with uv...
uv pip install -r requirements.txt

echo.
echo [SUCCESS] Setup complete!
echo You can now run 'start_server.bat' to start the crawler.
pause
