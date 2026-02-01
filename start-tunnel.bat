@echo off
title Cloudflare Tunnel - Backend
echo Starting Cloudflare Tunnel to http://127.0.0.1:8000
echo.
echo Make sure the backend is running first: run start-backend.bat
echo.
echo The tunnel URL will appear below. Use it in the driver app and update
echo the API URL in admin/passenger (or localStorage) if needed.
echo.
cloudflared tunnel --url http://127.0.0.1:8000 --protocol http2
pause
