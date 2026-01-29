@echo off
setlocal
cd /d "%~dp0"

set "GRADLE_HOME=%USERPROFILE%\.gradle\wrapper\dists\gradle-9.0.0-bin\d6wjpkvcgsg3oed0qlfss3wgl\gradle-9.0.0"
if not exist "%GRADLE_HOME%\bin\gradle.bat" (
    echo gradlew: Gradle not found at %GRADLE_HOME%
    echo Open project in Android Studio and sync to create the wrapper, or run build-apk.bat.
    exit /b 1
)

call "%GRADLE_HOME%\bin\gradle.bat" %*
exit /b %ERRORLEVEL%
