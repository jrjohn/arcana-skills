<#
.SYNOPSIS
  Optional Rust acceleration for claude-session-archive (Windows).

.DESCRIPTION
  Replaces the Python scripts with a single ~5 MB Rust binary `crs.exe`:
    build.py               → crs build
    embed_parallel.py      → crs embed-missing
    vsearch.py             → crs vsearch
    vsearch-since.py       → crs vsearch-since
    csearch.py             → crs csearch
    gen-recent-context.ps1 → crs gen-recent

  Speedups (measured Apple M4 — Windows similar):
    process startup       80ms  →  <5ms     >16×
    csearch (FTS5)        20ms  →  <5ms      >4×
    gen-recent SKIP path  10ms  →  <5ms     ~3-5×
    build steady-state   20-100ms → <5ms    5-20×
    gen-recent regen     340ms → 260ms      1.3× (Ollama-bound)
    build cold ingest    6.13s → 5.86s      1.05× (I/O-bound)

  Real value: single binary vs Python venv + sqlite_vec + requests deps.

  Run AFTER install.ps1 (base) and install-semantic.ps1 (Ollama).

.NOTES
  Requirements:
    - Rust toolchain (rustup-init.exe, then `rustup default stable`)
      https://rustup.rs
    - PowerShell execution policy: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

  Idempotent: re-running rebuilds + re-points hooks safely.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$SkillDir   = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Archive    = Join-Path $env:USERPROFILE 'claude-archive'
$SrcDir     = Join-Path $Archive 'crs'
$Bin        = Join-Path $SrcDir 'target\release\crs.exe'
$BinDir     = Join-Path $env:USERPROFILE 'bin'
$Settings   = Join-Path $env:USERPROFILE '.claude\settings.json'

Write-Host "==> install-rust-accel.ps1" -ForegroundColor Cyan
Write-Host "    skill source: $SkillDir"
Write-Host "    crs source:   $SrcDir"
Write-Host "    crs binary:   $Bin"

# 1. Sanity: cargo present
if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) {
    Write-Error "cargo not found. Install Rust via https://rustup.rs and re-run."
}
Write-Host "    cargo: $((& cargo --version))"

# 2. Copy crs source
New-Item -ItemType Directory -Force -Path (Join-Path $SrcDir 'src') | Out-Null
Copy-Item -Force (Join-Path $SkillDir 'scripts\crs\Cargo.toml')  (Join-Path $SrcDir 'Cargo.toml')
$lockSrc = Join-Path $SkillDir 'scripts\crs\Cargo.lock'
if (Test-Path $lockSrc) { Copy-Item -Force $lockSrc (Join-Path $SrcDir 'Cargo.lock') }
Copy-Item -Force (Join-Path $SkillDir 'scripts\crs\src\main.rs') (Join-Path $SrcDir 'src\main.rs')

# 3. Build release binary
Write-Host "==> cargo build --release  (first time ~2-5 min, deps cached afterwards)"
Push-Location $SrcDir
& cargo build --release
Pop-Location
$sizeMB = [math]::Round((Get-Item $Bin).Length / 1MB, 2)
Write-Host "    built: ${sizeMB} MB at $Bin"

# 4. Copy (not symlink — admin-only on Windows) to ~/bin
New-Item -ItemType Directory -Force -Path $BinDir | Out-Null
Copy-Item -Force $Bin (Join-Path $BinDir 'crs.exe')
Write-Host "    copied: $BinDir\crs.exe"
$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
if ($userPath -notlike "*$BinDir*") {
    Write-Host "    note: add $BinDir to PATH (User env)"
}

# 5. Rewire Scheduled Task: python build.py → crs.exe build
$TaskName = 'ClaudeArchiveIngest'
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "==> Rewiring Scheduled Task '$TaskName' to use crs.exe"
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    $action  = New-ScheduledTaskAction -Execute $Bin -Argument 'build'
    $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) `
                                        -RepetitionInterval (New-TimeSpan -Minutes 15)
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries `
                                              -DontStopIfGoingOnBatteries `
                                              -StartWhenAvailable `
                                              -ExecutionTimeLimit (New-TimeSpan -Minutes 30)
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
                           -Settings $settings -Description "Claude Code session JSONL ingest (Rust crs)" `
                           -RunLevel Limited | Out-Null
    Write-Host "    Scheduled Task rewired"
}

# 6. Rewire SessionStart hook: gen-recent-context.ps1 → crs.exe gen-recent
if (Test-Path $Settings) {
    $raw = Get-Content -Path $Settings -Raw
    if ($raw -match 'gen-recent-context\.ps1') {
        Write-Host "==> Rewiring SessionStart hook in $Settings"
        $obj = $raw | ConvertFrom-Json
        $newCmd = "`"$Bin`" gen-recent"
        $changed = 0
        if ($obj.hooks -and $obj.hooks.SessionStart) {
            foreach ($entry in $obj.hooks.SessionStart) {
                foreach ($h in $entry.hooks) {
                    if ($h.command -and $h.command -like '*gen-recent-context.ps1*') {
                        $h.command = $newCmd
                        $changed++
                    }
                }
            }
        }
        ($obj | ConvertTo-Json -Depth 10) | Set-Content -Path $Settings -Encoding UTF8
        Write-Host "    rewired $changed hook command(s)"
    } else {
        Write-Host "    SessionStart hook already on crs (or no .ps1 present)"
    }
}

# 7. Smoke test
Write-Host ""
Write-Host "==> smoke test:"
& $Bin --help | Select-Object -First 3
Write-Host ""
Write-Host "==> quick build (steady-state should be <100ms):"
$sw = [Diagnostics.Stopwatch]::StartNew()
& $Bin build --no-embed --no-refresh | Out-Null
$sw.Stop()
Write-Host "    elapsed: $([math]::Round($sw.Elapsed.TotalMilliseconds)) ms"

Write-Host ""
Write-Host "✓ Rust acceleration installed." -ForegroundColor Green
Write-Host "  - Scheduled Task: crs.exe build  (every 15 min)"
Write-Host "  - SessionStart:   crs.exe gen-recent"
Write-Host "  - interactive:    crs csearch / crs vsearch / crs vsearch-since"
Write-Host "  - python scripts still in $Archive (unused but kept for fallback)"
