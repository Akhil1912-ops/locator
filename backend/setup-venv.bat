@echo off
cd /d "%~dp0"
if exist .venv (
    echo Removing existing .venv...
    rd /s /q .venv
)
echo Creating virtual environment...
python -m venv .venv
if errorlevel 1 (
    echo venv failed. Try: python -m venv .venv --without-pip then install pip manually.
    exit /b 1
)
echo Installing dependencies...
.venv\Scripts\pip install -r requirements.txt
if errorlevel 1 (
    echo pip install failed.
    exit /b 1
)
echo Seeding database...
.venv\Scripts\python seed_db.py
if errorlevel 1 (
    echo seed_db failed.
    exit /b 1
)
echo.
echo Done. Run start-backend.bat to start the server.
pause
