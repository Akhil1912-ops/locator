@echo off
echo ============================================
echo   Bus Tracker - Start Backend + Tunnel
echo ============================================
echo.
echo Starting backend on port 8000...
cd /d %~dp0backend
start "Backend" cmd /k "call .venv\Scripts\activate && uvicorn app.main:app --host 0.0.0.0 --port 8000"
timeout /t 3 /nobreak > nul
echo.
echo Starting Cloudflare tunnel...
start "Tunnel" cmd /k "cloudflared tunnel --url http://127.0.0.1:8000 --protocol http2"
echo.
echo ============================================
echo   Two windows opened:
echo   1. Backend - keep running
echo   2. Tunnel - copy the https://xxx.trycloudflare.com URL
echo.
echo   Then use these links (replace TUNNEL_URL):
echo   Admin:    https://akhil1912-ops.github.io/locator/admin/?api=TUNNEL_URL
echo   Passenger: https://akhil1912-ops.github.io/locator/passenger/?api=TUNNEL_URL&bus=222
echo ============================================
pause
