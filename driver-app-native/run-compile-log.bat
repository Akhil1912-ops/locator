@echo off
cd /d "%~dp0"
echo Running Kotlin compile with --info to capture errors...
call gradlew.bat compileDebugKotlin --info > build-log.txt 2>&1
echo.
echo Full log written to build-log.txt
echo.
echo --- Lines containing "error" or "e: file" ---
findstr /i "e: file error Unresolved" build-log.txt
echo.
echo If you see Kotlin errors above, paste those lines when asking for help.
pause
