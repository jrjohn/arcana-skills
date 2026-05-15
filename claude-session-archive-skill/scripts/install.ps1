<#
.SYNOPSIS
  Base installer for claude-session-archive on Windows.

.DESCRIPTION
  Builds the Rust binary `crs.exe` (single ~5 MB self-contained binary, bundles
  SQLite + FTS5 + sqlite-vec) and wires up the 15-min ingest schedule.

  Steps:
    1. Verify cargo + sqlite3.exe in PATH
    2. mkdirs %USERPROFILE%\claude-archive, %USERPROFILE%\bin
    3. Copy crs source + cargo build --release
    4. Copy crs.exe + csearch.ps1 + vsearch.ps1 + sqliterc + gen-recent-context.ps1
    5. Add %USERPROFILE%\bin to user PATH
    6. Register Scheduled Task ClaudeArchiveIngest (every 15 min → crs.exe build)
    7. Register SessionStart hook (crs.exe gen-recent)
    7b. Install + register PreToolUse archive-preflight hook (Bash + Read)
    7c. Install + register UserPromptSubmit auto-vsearch-on-prompt hook
    8. First ingest run
    9. Smoke test

  Idempotent: re-running rebuilds + re-points hooks safely.

  AFTER this: optionally run install-semantic.ps1 to add Ollama + bge-m3 for
  semantic vsearch. Pure FTS5 csearch works without it.

.NOTES
  Requirements:
    - Rust toolchain (rustup-init.exe, then `rustup default stable`)
      https://rustup.rs
    - sqlite3.exe in PATH (winget install -e --id SQLite.SQLite)
    - PowerShell execution policy: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$SkillDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Archive  = Join-Path $env:USERPROFILE 'claude-archive'
$SrcDir   = Join-Path $Archive 'crs'
$Bin      = Join-Path $SrcDir 'target\release\crs.exe'
$BinDir   = Join-Path $env:USERPROFILE 'bin'
$Settings = Join-Path $env:USERPROFILE '.claude\settings.json'

Write-Host "==> install.ps1 — claude-session-archive base" -ForegroundColor Cyan
Write-Host "    skill source: $SkillDir"
Write-Host "    archive dir:  $Archive"
Write-Host "    crs binary:   $Bin"

# 1. Sanity checks — cargo strict; sqlite3 is recommended but optional
#    (crs.exe bundles SQLite, so csearch / vsearch work without sqlite3.exe;
#     it's only needed for raw `sqlite3 sessions.db` queries.)
if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) {
    Write-Error "cargo not found. Install Rust via https://rustup.rs and re-run."
}
Write-Host "    cargo:   $((& cargo --version))"

if (Get-Command sqlite3 -ErrorAction SilentlyContinue) {
    Write-Host "    sqlite3: $((& sqlite3 -version) | Select-Object -First 1)"
} else {
    Write-Host "    sqlite3: missing (optional — install with 'winget install -e --id SQLite.SQLite' if you want raw SQL queries)" -ForegroundColor Yellow
}

# 2. mkdirs
New-Item -ItemType Directory -Force -Path $Archive, $BinDir, (Join-Path $SrcDir 'src') | Out-Null

# 3. Copy crs source + build
Copy-Item -Force (Join-Path $SkillDir 'scripts\crs\Cargo.toml')  (Join-Path $SrcDir 'Cargo.toml')
$lockSrc = Join-Path $SkillDir 'scripts\crs\Cargo.lock'
if (Test-Path $lockSrc) { Copy-Item -Force $lockSrc (Join-Path $SrcDir 'Cargo.lock') }
Copy-Item -Force (Join-Path $SkillDir 'scripts\crs\src\main.rs') (Join-Path $SrcDir 'src\main.rs')

Write-Host "==> cargo build --release  (first time ~2-5 min, deps cached afterwards)"
Push-Location $SrcDir
& cargo build --release
Pop-Location
$sizeMB = [math]::Round((Get-Item $Bin).Length / 1MB, 2)
Write-Host "    built: ${sizeMB} MB at $Bin"

# 4. Copy artifacts
Write-Host "==> Installing artifacts to $BinDir + $Archive ..."
Copy-Item -Force $Bin (Join-Path $BinDir 'crs.exe')
Copy-Item -Force (Join-Path $SkillDir 'scripts\csearch.ps1') (Join-Path $BinDir 'csearch.ps1')
Copy-Item -Force (Join-Path $SkillDir 'scripts\vsearch.ps1') (Join-Path $BinDir 'vsearch.ps1')
Copy-Item -Force (Join-Path $SkillDir 'scripts\sqliterc.template') (Join-Path $env:USERPROFILE '.sqliterc')
Copy-Item -Force (Join-Path $SkillDir 'scripts\gen-recent-context.ps1') (Join-Path $Archive 'gen-recent-context.ps1')
Write-Host "    crs.exe + csearch.ps1 + vsearch.ps1 + .sqliterc + gen-recent-context.ps1 installed"

# 4b. (v1.15+) Install Windows OCR helper (Windows.Media.Ocr via PowerShell)
#     Built into Windows 10+ — no install, no engine to ship. The PS1 helper
#     uses WinRT projection to invoke OcrEngine on the image file.
Write-Host "==> Installing Windows OCR helper (Windows.Media.Ocr)"
$OcrBinDir = Join-Path $Archive 'bin'
$ImagesDir = Join-Path $Archive 'images'
New-Item -ItemType Directory -Force -Path $OcrBinDir, $ImagesDir | Out-Null
Copy-Item -Force (Join-Path $SkillDir 'scripts\ocr-win.ps1') (Join-Path $OcrBinDir 'ocr-win.ps1')
Write-Host "    OCR helper: $OcrBinDir\ocr-win.ps1"

# Verify pwsh 7+ is available — Windows.Media.Ocr WinRT projection needs it
$pwshPath = (Get-Command pwsh -ErrorAction SilentlyContinue)?.Source
if (-not $pwshPath) {
    Write-Host "    !! pwsh (PowerShell 7+) missing — install: winget install --id Microsoft.PowerShell" -ForegroundColor Yellow
    Write-Host "       OCR helper won't work under Windows PowerShell 5.x (built-in)"
} else {
    Write-Host "    pwsh: $pwshPath"
}

# 4c. (PG-backend) Apply image_ocr schema migration via psql, if reachable
$psql = (Get-Command psql -ErrorAction SilentlyContinue)?.Source
if ($psql -and $env:CRS_PG_PASSWORD) {
    $pgHost = if ($env:CRS_PG_HOST) { $env:CRS_PG_HOST } else { 'localhost' }
    $pgPort = if ($env:CRS_PG_PORT) { $env:CRS_PG_PORT } else { '5432' }
    $pgUser = if ($env:CRS_PG_USER) { $env:CRS_PG_USER } else { 'archive' }
    $pgDb   = if ($env:CRS_PG_DB)   { $env:CRS_PG_DB   } else { 'archive_main' }
    $sqlFile = Join-Path $SkillDir 'sql\image_ocr.sql'
    Write-Host "==> applying image_ocr schema to PG (idempotent)"
    $env:PGPASSWORD = $env:CRS_PG_PASSWORD
    & $psql -h $pgHost -p $pgPort -U $pgUser -d $pgDb -v ON_ERROR_STOP=1 -f $sqlFile | Out-Null
    Write-Host "    image_ocr_cache + image_ocr tables ready on $pgHost/$pgDb"
} else {
    Write-Host "    !! psql or CRS_PG_PASSWORD missing — apply image_ocr schema manually:" -ForegroundColor Yellow
    Write-Host "       psql ... -f $SkillDir\sql\image_ocr.sql"
}

# 5. Add %USERPROFILE%\bin to user PATH if missing
$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
if ($userPath -notlike "*$BinDir*") {
    Write-Host "==> Adding $BinDir to user PATH ..."
    [Environment]::SetEnvironmentVariable('Path', "$userPath;$BinDir", 'User')
    Write-Host "    Re-open terminal to pick up new PATH."
}

# 6. Register Scheduled Task — crs.exe build every 15 min
Write-Host "==> Registering Scheduled Task 'ClaudeArchiveIngest' (every 15 min) ..."
$taskName = 'ClaudeArchiveIngest'
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing) { Unregister-ScheduledTask -TaskName $taskName -Confirm:$false }

$action  = New-ScheduledTaskAction -Execute $Bin -Argument 'build'
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) `
                                    -RepetitionInterval (New-TimeSpan -Minutes 15)
$tsetting = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries `
                                          -DontStopIfGoingOnBatteries `
                                          -StartWhenAvailable `
                                          -ExecutionTimeLimit (New-TimeSpan -Minutes 30)
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger `
                       -Settings $tsetting -Description "Claude Code session JSONL → SQLite FTS5 ingest (Rust crs)" `
                       -RunLevel Limited | Out-Null

# 7. Register SessionStart hook
$hookCmd = "`"$Bin`" gen-recent"
if (-not (Test-Path $Settings)) {
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Settings) | Out-Null
    '{}' | Set-Content -Path $Settings -Encoding UTF8
}
try {
    $obj = Get-Content -Path $Settings -Raw | ConvertFrom-Json
} catch {
    $obj = [PSCustomObject]@{}
}
if (-not $obj.PSObject.Properties['hooks']) {
    $obj | Add-Member -NotePropertyName hooks -NotePropertyValue ([PSCustomObject]@{})
}
if (-not $obj.hooks.PSObject.Properties['SessionStart']) {
    $obj.hooks | Add-Member -NotePropertyName SessionStart -NotePropertyValue @()
}
$alreadyRegistered = $false
foreach ($entry in @($obj.hooks.SessionStart)) {
    foreach ($h in @($entry.hooks)) {
        if ($h.command -and ($h.command -like '*crs*gen-recent*' -or $h.command -like '*gen-recent-context*')) {
            $alreadyRegistered = $true
        }
    }
}
if ($alreadyRegistered) {
    Write-Host "    SessionStart hook already registered (skip)"
} else {
    $newEntry = [PSCustomObject]@{
        hooks = @(
            [PSCustomObject]@{ type = 'command'; command = $hookCmd; timeout = 30 }
        )
    }
    $obj.hooks.SessionStart = @($obj.hooks.SessionStart) + $newEntry
    ($obj | ConvertTo-Json -Depth 10) | Set-Content -Path $Settings -Encoding UTF8
    Write-Host "==> SessionStart hook registered in $Settings"
}

# 7b. Install + register archive-preflight PreToolUse hook
#     - Blocks raw sqlite3 against archive DB until vsearch/csearch runs once.
#     - Blocks grep/Select-String/Read on memory files until vsearch/csearch runs once.
#     - Sentinel: $env:TEMP\claude-archive-preflight-<session_id>
$HooksDir  = Join-Path $env:USERPROFILE '.claude\hooks'
$Preflight = Join-Path $HooksDir 'archive-preflight.ps1'
New-Item -ItemType Directory -Force -Path $HooksDir | Out-Null
Write-Host "==> installing archive-preflight hook → $Preflight"
Copy-Item -Force (Join-Path $SkillDir 'scripts\archive-preflight.ps1') $Preflight

# Re-load $obj to pick up SessionStart edit above
$obj = Get-Content -Path $Settings -Raw | ConvertFrom-Json
if (-not $obj.PSObject.Properties['hooks']) {
    $obj | Add-Member -NotePropertyName hooks -NotePropertyValue ([PSCustomObject]@{})
}
if (-not $obj.hooks.PSObject.Properties['PreToolUse']) {
    $obj.hooks | Add-Member -NotePropertyName PreToolUse -NotePropertyValue @()
}

$preflightCmd = "powershell -NoProfile -ExecutionPolicy Bypass -File `"$Preflight`""
foreach ($matcher in 'Bash','Read') {
    $alreadyRegistered = $false
    foreach ($entry in @($obj.hooks.PreToolUse)) {
        if ($entry.matcher -eq $matcher) {
            foreach ($h in @($entry.hooks)) {
                if ($h.command -and ($h.command -like "*archive-preflight.ps1*")) {
                    $alreadyRegistered = $true
                }
            }
        }
    }
    if ($alreadyRegistered) {
        Write-Host "    PreToolUse $matcher hook already registered (skip)"
    } else {
        $newPre = [PSCustomObject]@{
            matcher = $matcher
            hooks   = @(
                [PSCustomObject]@{ type = 'command'; command = $preflightCmd; timeout = 5 }
            )
        }
        $obj.hooks.PreToolUse = @($obj.hooks.PreToolUse) + $newPre
        Write-Host "==> registering PreToolUse $matcher hook"
    }
}
($obj | ConvertTo-Json -Depth 10) | Set-Content -Path $Settings -Encoding UTF8

# 7c. Install + register auto-vsearch-on-prompt UserPromptSubmit hook
#     - Pattern-matches identity / history / status / question keywords in the
#       prompt and pre-runs vsearch, injecting top hits as additionalContext.
#     - Also pre-sets the preflight sentinel so subsequent sqlite3 / memory
#       grep / SSH log queries unblock automatically.
#     - Don't clobber a customized auto-vsearch-on-prompt.ps1 (preserve user
#       customizations, e.g. an extra trigger branch).
$AutoVsearch = Join-Path $HooksDir 'auto-vsearch-on-prompt.ps1'
$AutoVsearchSrc = Join-Path $SkillDir 'scripts\auto-vsearch-on-prompt.ps1'
if (Test-Path $AutoVsearch) {
    $srcHash = (Get-FileHash $AutoVsearchSrc).Hash
    $dstHash = (Get-FileHash $AutoVsearch).Hash
    if ($srcHash -eq $dstHash) {
        Write-Host "    auto-vsearch-on-prompt hook unchanged: $AutoVsearch"
    } else {
        Write-Host "    !! $AutoVsearch exists and differs from skill version — leaving as-is"
        Write-Host "       (your version may have local customizations like a luminous-skill"
        Write-Host "       trigger; diff manually if needed)"
    }
} else {
    Write-Host "==> installing auto-vsearch-on-prompt hook → $AutoVsearch"
    Copy-Item -Force $AutoVsearchSrc $AutoVsearch
}

# Re-load $obj to pick up PreToolUse edits above
$obj = Get-Content -Path $Settings -Raw | ConvertFrom-Json
if (-not $obj.PSObject.Properties['hooks']) {
    $obj | Add-Member -NotePropertyName hooks -NotePropertyValue ([PSCustomObject]@{})
}
if (-not $obj.hooks.PSObject.Properties['UserPromptSubmit']) {
    $obj.hooks | Add-Member -NotePropertyName UserPromptSubmit -NotePropertyValue @()
}

$autoVsearchCmd = "powershell -NoProfile -ExecutionPolicy Bypass -File `"$AutoVsearch`""
$alreadyRegistered = $false
foreach ($entry in @($obj.hooks.UserPromptSubmit)) {
    foreach ($h in @($entry.hooks)) {
        if ($h.command -and ($h.command -like '*auto-vsearch-on-prompt.ps1*')) {
            $alreadyRegistered = $true
        }
    }
}
if ($alreadyRegistered) {
    Write-Host "    UserPromptSubmit auto-vsearch hook already registered (skip)"
} else {
    $newUps = [PSCustomObject]@{
        hooks = @(
            [PSCustomObject]@{ type = 'command'; command = $autoVsearchCmd; timeout = 5 }
        )
    }
    $obj.hooks.UserPromptSubmit = @($obj.hooks.UserPromptSubmit) + $newUps
    Write-Host "==> registering UserPromptSubmit auto-vsearch hook"
    ($obj | ConvertTo-Json -Depth 10) | Set-Content -Path $Settings -Encoding UTF8
}

# 8. First ingest
Write-Host "==> First ingest ..."
& $Bin build --no-embed

# 9. Smoke test
Write-Host ""
Write-Host "==> smoke test:"
& $Bin --help | Select-Object -First 3

Write-Host ""
Write-Host "✓ Base install complete." -ForegroundColor Green
Write-Host "  - 15-min ingest:        Get-ScheduledTask -TaskName ClaudeArchiveIngest"
Write-Host "  - SessionStart hook:    crs.exe gen-recent"
Write-Host "  - PreToolUse hook:      $Preflight (Bash + Read; vsearch/csearch preflight)"
Write-Host "  - UserPromptSubmit:     $AutoVsearch (auto-vsearch on identity/history/status prompts)"
Write-Host "  - interactive:          csearch.ps1 / vsearch.ps1 / crs csearch / crs vsearch"
Write-Host ""
Write-Host "Optional next step (semantic search via Ollama + bge-m3):"
Write-Host "  .\install-semantic.ps1          # native OllamaSetup.exe"
Write-Host "  .\install-semantic-docker.ps1   # Docker Desktop variant"
