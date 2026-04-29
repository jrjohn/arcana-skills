<#
.SYNOPSIS
  Windows port of gen-recent-context.sh — auto-generate per-project recent context for Memory.

.DESCRIPTION
  Triggered by SessionStart hook + every-15-min crs build task. Writes a
  single section: vsearch ranking of last-48h msgs against the project's
  pending list. Pending excerpt itself is NOT duplicated — Claude reads
  project_pending.md directly via MEMORY.md index when it needs that.

  Skip guard:
    regen only if (pending mtime > auto_recent mtime)
                  OR (newest msg ts > auto_recent mtime)
                  OR ($env:FORCE_REGEN -eq '1')
    Otherwise exit early without touching Ollama / KNN / disk write.

  Writes %USERPROFILE%\.claude\projects\<slug>\memory\auto_recent.md

  Slug source (priority):
    1. $env:CLAUDE_PROJECT_SLUG       ← used by crs build 15-min loop
    2. JSON on stdin: {"cwd": "..."}  ← SessionStart hook input
    3. $env:CLAUDE_PROJECT_DIR
    4. $PWD                           ← interactive fallback

  Exits silently if the resolved project has no memory dir.

.PARAMETER Force
  Override skip guard (same as $env:FORCE_REGEN=1).
#>
[CmdletBinding()]
param([switch]$Force)

$ErrorActionPreference = 'Stop'

$Archive = Join-Path $env:USERPROFILE 'claude-archive'
$Db      = Join-Path $Archive 'sessions.db'
$LogFile = Join-Path $Archive 'gen-recent-context.log'

function Write-Log {
    param([string]$Level, [string]$Message)
    $ts = Get-Date -Format 'yyyy-MM-ddTHH:mm:ss'
    Add-Content -Path $LogFile -Value "$ts [$Level] $Message" -Encoding UTF8
}

trap {
    Write-Log -Level 'ERROR' -Message "uncaught failure: $($_.Exception.Message)"
    exit 1
}

if (-not (Test-Path $Db)) {
    Write-Log -Level 'SKIP' -Message 'no session.db'
    Write-Host '(no session.db, skipping)'
    exit 0
}

# 1. Resolve slug
$Slug = $env:CLAUDE_PROJECT_SLUG
if (-not $Slug) {
    $ProjectDir = $null

    # Try stdin JSON (SessionStart hook input)
    if ([Console]::IsInputRedirected) {
        try {
            $stdin = [Console]::In.ReadToEnd()
            if ($stdin) {
                $obj = $stdin | ConvertFrom-Json -ErrorAction SilentlyContinue
                if ($obj -and $obj.cwd) { $ProjectDir = $obj.cwd }
            }
        } catch { }
    }

    if (-not $ProjectDir) { $ProjectDir = $env:CLAUDE_PROJECT_DIR }
    if (-not $ProjectDir) { $ProjectDir = (Get-Location).Path }

    # Slug = path with both / and \ replaced by -, drive colon stripped
    $Slug = $ProjectDir -replace '[/\\]', '-' -replace ':', ''
}

$MemDir  = Join-Path $env:USERPROFILE ".claude\projects\$Slug\memory"
$Pending = Join-Path $MemDir 'project_pending.md'
$OutFile = Join-Path $MemDir 'auto_recent.md'

if (-not (Test-Path $MemDir)) {
    Write-Log -Level 'SKIP' -Message "unknown project slug=$Slug (no memory dir)"
    exit 0
}

# 2. Skip guard
$forceRegen = $Force -or ($env:FORCE_REGEN -eq '1')
if (-not $forceRegen -and (Test-Path $OutFile)) {
    $lastGenTs   = [int][double]::Parse((Get-Item $OutFile).LastWriteTimeUtc.Subtract([datetime]'1970-01-01').TotalSeconds)
    $pendingTs   = 0
    if (Test-Path $Pending) {
        $pendingTs = [int][double]::Parse((Get-Item $Pending).LastWriteTimeUtc.Subtract([datetime]'1970-01-01').TotalSeconds)
    }

    $latestMsgTs = 0
    try {
        $sql = "SELECT IFNULL(strftime('%s', MAX(ts)), 0) FROM msg WHERE project='$Slug'"
        $latestMsgTs = [int](& sqlite3 $Db $sql 2>$null)
    } catch { }

    if ($pendingTs -le $lastGenTs -and $latestMsgTs -le $lastGenTs) {
        Write-Log -Level 'SKIP' -Message "no changes (slug=$Slug, last_gen=$lastGenTs, pending=$pendingTs, latest_msg=$latestMsgTs)"
        exit 0
    }
}

# 3. Generate
$Now    = Get-Date -Format 'yyyy-MM-dd HH:mm'
$CrsBin = Join-Path $Archive 'crs\target\release\crs.exe'

$lines = @()
$lines += '---'
$lines += 'name: 自動最近 context'
$lines += 'description: 最近 48h 跟 pending 語意相關的對話 snippets（vsearch ranking）。pending 條目本身請讀 project_pending.md，不要兩邊都讀'
$lines += 'type: project'
$lines += 'auto-generated: true'
$lines += "last-update: $Now"
$lines += '---'
$lines += ''
$lines += '# 🔄 最近 48h 跟 pending 語意相關的訊息'
$lines += ''
$lines += '> vsearch on pending → KNN over msg_vec (cosine, max-distance 0.65)。'
$lines += "> project=``$Slug``。要改邏輯動 ``gen-recent-context.ps1``。"
$lines += ''

if (-not (Test-Path $CrsBin)) {
    $lines += '_(vsearch-since 不可用：crs binary 缺)_'
} elseif (-not (Test-Path $Pending)) {
    $lines += '_(無 pending 檔可當 query seed)_'
} else {
    # Extract "## 待處理" section from pending — strip markdown decoration, cap at 1500 chars
    $pendingText = Get-Content -Path $Pending -Raw -Encoding UTF8
    $query = ''
    $inSection = $false
    foreach ($line in $pendingText -split "`r?`n") {
        if ($line -match '^## 待處理') { $inSection = $true; continue }
        if ($inSection -and $line -match '^## ') { break }
        if ($inSection) { $query += $line + ' ' }
    }
    $query = ($query -replace '[*#`]', '').Trim()
    if ($query.Length -gt 1500) { $query = $query.Substring(0, 1500) }

    if (-not $query) {
        $lines += '_(pending list 空，無 query seed)_'
    } else {
        try {
            $vsOutput = & $CrsBin vsearch-since `
                "--query=$query" `
                "--project=$Slug" `
                '--hours=48' `
                '--limit=6' `
                '--max-distance=0.65' `
                '--max-snippet=140' 2>&1
            if ($LASTEXITCODE -ne 0) {
                Write-Log -Level 'ERROR' -Message "vsearch-since exit=$LASTEXITCODE: $vsOutput"
                $lines += "_(vsearch-since 失敗 — 看 $LogFile)_"
            } else {
                $lines += $vsOutput
            }
        } catch {
            Write-Log -Level 'ERROR' -Message "vsearch-since exception: $($_.Exception.Message)"
            $lines += "_(vsearch-since 失敗 — 看 $LogFile)_"
        }
    }
}

$lines += ''
$lines += '---'
$lines += '*Regen on SessionStart + 15-min task, with skip guard. Force: `$env:FORCE_REGEN=1; ~\claude-archive\gen-recent-context.ps1`*'

# Write atomically (UTF8 no BOM)
$utf8 = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllLines($OutFile, $lines, $utf8)

Write-Log -Level 'OK' -Message "wrote $OutFile ($($lines.Count) lines, project=$Slug)"
Write-Host "wrote $OutFile ($($lines.Count) lines, project=$Slug)"
