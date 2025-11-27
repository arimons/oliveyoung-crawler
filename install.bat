@echo off
chcp 65001 >nul
setlocal enableDelayedExpansion

REM 변수 설정
set "REPO_URL=https://github.com/arimons/oliveyoung-crawler.git"
set "REPO_NAME=oliveyoung-crawler"
set "VENV_DIR=venv"
set "PYTHON_EXEC="

ECHO =========================================================
ECHO 🛒 Olive Young Crawler - Installation
ECHO =========================================================

REM --- 1. Git Clone (프로젝트 폴더 존재 여부 확인) ---
if exist "%REPO_NAME%" (
    ECHO.
    ECHO [1/6] ✅ Repository folder "%REPO_NAME%" already exists. Skipping Git Clone.
    cd "%REPO_NAME%"
) else (
    ECHO.
    ECHO [1/6] ⬇️ Cloning repository from GitHub...
    git clone %REPO_URL%
    IF ERRORLEVEL 1 (
        ECHO ❌ ERROR: Git Clone failed. Check Git installation and internet connection.
        GOTO :END
    )
    cd "%REPO_NAME%"
)

IF ERRORLEVEL 1 (
    ECHO ❌ FATAL ERROR: Cannot navigate to project folder.
    GOTO :END
)

REM --- 2. Python 찾기 (py launcher 또는 python 명령) ---
ECHO.
ECHO [2/6] 🔍 Searching for Python...

py --version >nul 2>&1
IF ERRORLEVEL 0 (
    set "PYTHON_EXEC=py"
    ECHO ✅ Found Python via 'py' launcher.
) ELSE (
    python --version >nul 2>&1
    IF ERRORLEVEL 0 (
        set "PYTHON_EXEC=python"
        ECHO ✅ Found Python via 'python' command.
    ) ELSE (
        ECHO ❌ ERROR: Python not found. Please install Python 3.8 or higher.
        GOTO :END
    )
)

REM --- 3. Virtual Environment Creation ---
if exist "%VENV_DIR%" (
    ECHO.
    ECHO [3/6] ✅ Virtual environment "%VENV_DIR%" already exists. Skipping creation.
) else (
    ECHO.
    ECHO [3/6] 🛠️ Creating virtual environment using %PYTHON_EXEC%...
    %PYTHON_EXEC% -m venv "%VENV_DIR%"
    IF ERRORLEVEL 1 (
        ECHO ❌ ERROR: Virtual environment creation failed.
        GOTO :END
    )
)

REM --- 4. Activate Virtual Environment ---
ECHO.
ECHO [4/6] 🟢 Activating virtual environment...
call "%VENV_DIR%\Scripts\activate"
IF ERRORLEVEL 1 (
    ECHO ❌ ERROR: Virtual environment activation failed.
    GOTO :END
)

REM --- 5. Install UV and Dependencies ---
ECHO.
ECHO [5/6] 📦 Installing UV for fast package management...
pip install uv
IF ERRORLEVEL 1 (
    ECHO ⚠️ WARNING: UV installation failed. Falling back to pip...
    ECHO [5/6] 📦 Installing packages with pip...
    pip install -r requirements.txt
    IF ERRORLEVEL 1 (
        ECHO ❌ ERROR: Package installation failed.
        GOTO :END
    )
) ELSE (
    ECHO [5/6] 📦 Installing packages with UV...
    uv pip install -r requirements.txt
    IF ERRORLEVEL 1 (
        ECHO ❌ ERROR: Package installation failed.
        GOTO :END
    )
)

REM --- 6. Create Desktop Shortcut ---
ECHO.
ECHO [6/6] 🔗 Creating Desktop Shortcut...

set "CURRENT_DIR=%CD%"
set "TARGET_SCRIPT=%CURRENT_DIR%\start_server.bat"
set "SHORTCUT_NAME=Olive Young Crawler.lnk"
set "DESKTOP=%USERPROFILE%\Desktop"

REM PowerShell로 바로가기 생성 (경로 이스케이프 처리)
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%DESKTOP%\%SHORTCUT_NAME%'); $s.TargetPath = '%TARGET_SCRIPT%'; $s.WorkingDirectory = '%CURRENT_DIR%'; $s.Save()"

IF ERRORLEVEL 1 (
    ECHO ⚠️ WARNING: Desktop shortcut creation failed. You can manually run start_server.bat
) ELSE (
    ECHO ✅ Desktop shortcut created successfully!
)

ECHO.
ECHO =========================================================
ECHO ✅ Installation Complete!
ECHO =========================================================
ECHO.
ECHO You can now:
ECHO   1. Run 'start_server.bat' in this folder
ECHO   2. Or use the Desktop shortcut 'Olive Young Crawler'
ECHO.
ECHO The server will open at: http://localhost:8000
ECHO =========================================================

:END
ECHO.
PAUSE
