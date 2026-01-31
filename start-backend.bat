@echo off
echo Starting Backend Server...
echo.
cd /d %~dp0backend
call .venv\Scripts\activate
REM Use --reload only if you need auto-restart on code changes (can cause issues on Windows)
uvicorn app.main:app --host 0.0.0.0 --port 8000

