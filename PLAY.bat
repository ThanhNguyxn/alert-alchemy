@echo off
REM ═══════════════════════════════════════════════════════
REM  🧪 Alert Alchemy - One-Click Play
REM ═══════════════════════════════════════════════════════
cd /d "%~dp0"

REM Check if executable exists
if not exist "alert-alchemy.exe" (
    echo ERROR: alert-alchemy.exe not found!
    echo Make sure you extracted all files from the zip.
    pause
    exit /b 1
)

REM Start interactive play mode
alert-alchemy.exe play
pause
