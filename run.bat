@echo off
cd /d "%~dp0"

where python >nul 2>nul
if %errorlevel% neq 0 (
    where py >nul 2>nul
    if %errorlevel% neq 0 (
        echo Python is required but was not found.
        echo Please install Python 3.
        pause
        exit /b 1
    )
    py launcher.py
) else (
    python launcher.py
)

pause