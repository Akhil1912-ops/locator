@echo off
echo Starting Admin Panel Server...
echo.
echo Open http://localhost:3001/index.html in your browser
echo.
echo Press Ctrl+C to stop the server
echo.
cd /d %~dp0
python -m http.server 3001

