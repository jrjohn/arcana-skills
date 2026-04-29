<#
.SYNOPSIS
  Windows installer for claude-session-archive-skill base setup.

.DESCRIPTION
  Counterpart to README.md "Quick install" bash steps. Sets up:
    - %USERPROFILE%\claude-archive\ (mkdirs)
    - build.py + sqliterc.template into %USERPROFILE%\claude-archive\
    - csearch.ps1 / vsearch.ps1 into %USERPROFILE%\bin\ (added to PATH)
    - Scheduled Task "ClaudeArchiveIngest" — runs build.py every 15 min
    - Initial ingest run

  Run from inside cloned arcana-skills/claude-session-archive-skill/scripts/.

.NOTES
  Requirements (verify before running):
    - Python 3.11+ in PATH (python --version)
    - sqlite3.exe in PATH (winget install -e --id SQLite.SQLite, or download)
    - PowerShell execution policy allows local scripts:
        Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

  After install, run install-semantic.ps1 (optional) for Ollama-based vsearch.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$SkillDir   = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Archive    = Join-Path $env:USERPROFILE 'claude-archive'
$BinDir     = Join-Path $env:USERPROFILE 'bin'

Write-Host "==> Installing claude-session-archive-skill (base)" -ForegroundColor Cyan
Write-Host "    Skill source: $SkillDir"
Write-Host "    Archive dir:  $Archive"
Write-Host "    Bin dir:      $BinDir"

# 0. Sanity checks
foreach ($cmd in 'python','sqlite3') {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        Write-Error "$cmd not found in PATH. Install before running."
    }
}

# 1. mkdirs
New-Item -ItemType Directory -Force -Path $Archive, $BinDir | Out-Null

# 2. copy scripts
Write-Host "==> Copying build.py + sqliterc.template ..."
Copy-Item -Force (Join-Path $SkillDir 'scripts\build.py')           (Join-Path $Archive 'build.py')
Copy-Item -Force (Join-Path $SkillDir 'scripts\sqliterc.template')  (Join-Path $env:USERPROFILE '.sqliterc')

# 3. CLI wrappers
Write-Host "==> Copying csearch.ps1 + vsearch.ps1 to $BinDir ..."
Copy-Item -Force (Join-Path $SkillDir 'scripts\csearch.ps1') (Join-Path $BinDir 'csearch.ps1')
Copy-Item -Force (Join-Path $SkillDir 'scripts\vsearch.ps1') (Join-Path $BinDir 'vsearch.ps1')

# 4. add ~/bin to user PATH if not already
$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
if ($userPath -notlike "*$BinDir*") {
    Write-Host "==> Adding $BinDir to user PATH ..."
    [Environment]::SetEnvironmentVariable('Path', "$userPath;$BinDir", 'User')
    Write-Host "    Re-open terminal to pick up new PATH."
}

# 5. first ingest
Write-Host "==> Running first ingest (may take 30-60 sec on fresh DB)..."
& python (Join-Path $Archive 'build.py')

# 5a. SessionStart hook for auto_recent.md (Windows uses gen-recent-context.ps1 — TODO: port; for now just install bash version usable from WSL)
$ctxScript = Join-Path $SkillDir 'scripts\gen-recent-context.sh'
if (Test-Path $ctxScript) {
    Copy-Item -Force $ctxScript (Join-Path $Archive 'gen-recent-context.sh')
    Write-Host "==> gen-recent-context.sh installed (Windows users: requires WSL or Git Bash to execute)"
}

# 6. register scheduled task — runs every 15 min
Write-Host "==> Registering Scheduled Task 'ClaudeArchiveIngest' (every 15 min)..."
$taskName = 'ClaudeArchiveIngest'
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing) { Unregister-ScheduledTask -TaskName $taskName -Confirm:$false }

$pythonExe = (Get-Command python).Source
$action  = New-ScheduledTaskAction -Execute $pythonExe -Argument "`"$Archive\build.py`""
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) `
                                    -RepetitionInterval (New-TimeSpan -Minutes 15)
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries `
                                          -DontStopIfGoingOnBatteries `
                                          -StartWhenAvailable `
                                          -ExecutionTimeLimit (New-TimeSpan -Minutes 30)
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger `
                       -Settings $settings -Description "Claude Code session JSONL → SQLite FTS5 ingest" `
                       -RunLevel Limited | Out-Null

Write-Host ""
Write-Host "✓ Base install complete." -ForegroundColor Green
Write-Host "  Test:    csearch.ps1 claude"
Write-Host "  Verify:  Get-ScheduledTask -TaskName ClaudeArchiveIngest"
Write-Host ""
Write-Host "Next step (optional, semantic search):"
Write-Host "  .\install-semantic.ps1"
