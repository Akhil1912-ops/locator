@echo off
setlocal
cd /d "%~dp0"

:: Use gradlew if available (e.g. after Android Studio sync)
if exist "gradlew.bat" (
    echo Using Gradle wrapper...
    echo Stopping any running Gradle daemons...
    call gradlew.bat --stop 2>nul
    call gradlew.bat assembleDebug
    goto :done
)

:: Otherwise use Gradle from user's .gradle cache (e.g. from Android Studio)
set "GRADLE_HOME=%USERPROFILE%\.gradle\wrapper\dists\gradle-9.0.0-bin\d6wjpkvcgsg3oed0qlfss3wgl\gradle-9.0.0"
if exist "%GRADLE_HOME%\bin\gradle.bat" (
    echo Using local Gradle 9.0.0...
    call "%GRADLE_HOME%\bin\gradle.bat" assembleDebug --no-daemon
    goto :done
)

:: Fallback: try any gradle-9* in dists
for /d %%D in ("%USERPROFILE%\.gradle\wrapper\dists\gradle-9*-bin\*\gradle-9*") do (
    if exist "%%~D\bin\gradle.bat" (
        echo Using %%D...
        call "%%~D\bin\gradle.bat" assembleDebug
        goto :done
    )
)

echo.
echo Gradle wrapper not found. Do this:
echo   1. Open this folder in Android Studio (File, Open, driver-app-native).
echo   2. Let Gradle sync.
echo   3. Build, Build Bundle(s) / APK(s), Build APK(s).
echo   APK output: app\build\outputs\apk\debug\app-debug.apk
echo.
echo Or create the wrapper: run "gradle wrapper" here (if you have Gradle installed), then run this script again.
exit /b 1

:done
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
echo.
echo Build complete. APK: app\build\outputs\apk\debug\app-debug.apk
exit /b 0
