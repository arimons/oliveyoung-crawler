@echo off
chcp 65001 >nul
echo ==========================================
echo   Olive Young Crawler Server
echo ==========================================

cd /d "%~dp0"

echo [INFO] Checking for updates...
git pull origin main
echo.

if not exist venv (
    echo [ERROR] Virtual environment not found.
    echo Please run 'install.bat' first.
    pause
    exit /b
)

call venv\Scripts\activate

echo [INFO] Starting server...
echo [INFO] Open http://127.0.0.1:8000 in your browser
python run_server.py

pause
