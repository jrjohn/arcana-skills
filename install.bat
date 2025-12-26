@echo off
REM ============================================================================
REM Arcana Skills Installer for Claude Code (Windows Batch Wrapper)
REM ============================================================================
REM
REM This batch file launches the PowerShell installer.
REM Can be run from Command Prompt (cmd.exe) or by double-clicking.
REM
REM Usage:
REM   install.bat           - Interactive installation
REM   install.bat -All      - Install all skills
REM   install.bat -WSL      - Install to WSL2
REM   install.bat -WSL -All - Install all to WSL2
REM
REM One-line install from cmd.exe:
REM   curl -fsSL https://raw.githubusercontent.com/jrjohn/arcana-skills/main/install.bat -o install.bat && install.bat
REM
REM ============================================================================

setlocal enabledelayedexpansion

REM Check PowerShell availability
where pwsh >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set "PS_EXE=pwsh"
    goto :found_ps
)

where powershell >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set "PS_EXE=powershell"
    goto :found_ps
)

echo [ERROR] PowerShell is not installed or not in PATH.
echo Please install PowerShell first.
pause
exit /b 1

:found_ps
REM Get script directory
set "SCRIPT_DIR=%~dp0"

REM Check if install.ps1 exists locally
if exist "%SCRIPT_DIR%install.ps1" (
    echo [INFO] Running local installer...
    %PS_EXE% -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%install.ps1" %*
    set "INSTALL_RESULT=!ERRORLEVEL!"
) else (
    echo [INFO] Downloading installer...
    %PS_EXE% -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/jrjohn/arcana-skills/main/install.ps1' -OutFile '%TEMP%\arcana-install.ps1'; exit $LASTEXITCODE"
    if !ERRORLEVEL! NEQ 0 (
        echo [ERROR] Failed to download installer.
        pause
        exit /b 1
    )
    %PS_EXE% -NoProfile -ExecutionPolicy Bypass -File "%TEMP%\arcana-install.ps1" %*
    set "INSTALL_RESULT=!ERRORLEVEL!"
)

REM Clean up temp file if it exists
if exist "%TEMP%\arcana-install.ps1" del /q "%TEMP%\arcana-install.ps1" 2>nul

if !INSTALL_RESULT! NEQ 0 (
    echo.
    echo [ERROR] Installation failed. Error code: !INSTALL_RESULT!
    echo.
    echo Troubleshooting:
    echo   1. Ensure you have administrator privileges if needed
    echo   2. Check that git is installed: git --version
    echo   3. Try running PowerShell as Administrator
    echo   4. Run install.ps1 directly in PowerShell:
    echo      powershell -ExecutionPolicy Bypass -File install.ps1
    echo.
    pause
    exit /b !INSTALL_RESULT!
)

echo.
echo Installation completed successfully!
echo.
pause
