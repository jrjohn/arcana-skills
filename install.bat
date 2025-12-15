@echo off
REM ============================================================================
REM Arcana Skills Installer for Claude Code (Windows Batch Wrapper)
REM ============================================================================
REM
REM This batch file launches the PowerShell installer.
REM
REM Usage:
REM   install.bat           - Interactive installation
REM   install.bat -All      - Install all skills
REM   install.bat -WSL      - Install to WSL2
REM   install.bat -WSL -All - Install all to WSL2
REM
REM ============================================================================

setlocal enabledelayedexpansion

REM Check PowerShell availability
where pwsh >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set "PS_EXE=pwsh"
) else (
    where powershell >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        set "PS_EXE=powershell"
    ) else (
        echo [ERROR] PowerShell is not installed or not in PATH.
        echo Please install PowerShell or run install.ps1 directly.
        exit /b 1
    )
)

REM Get script directory
set "SCRIPT_DIR=%~dp0"

REM Check if install.ps1 exists locally
if exist "%SCRIPT_DIR%install.ps1" (
    echo [INFO] Running local installer...
    %PS_EXE% -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%install.ps1" %*
) else (
    echo [INFO] Downloading and running installer...
    %PS_EXE% -NoProfile -ExecutionPolicy Bypass -Command "& { iwr -useb 'https://raw.githubusercontent.com/jrjohn/arcana-skills/main/install.ps1' | iex }"
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Installation failed. Error code: %ERRORLEVEL%
    echo.
    echo Troubleshooting:
    echo   1. Ensure you have administrator privileges if needed
    echo   2. Check that git is installed: git --version
    echo   3. Try running PowerShell as Administrator
    echo   4. Run install.ps1 directly: powershell -File install.ps1
    echo.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo Installation completed successfully!
echo.
pause
