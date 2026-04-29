<#
.SYNOPSIS
  csearch — FTS5 lexical search over Claude session archive.

.DESCRIPTION
  Windows PowerShell counterpart to scripts/csearch (bash).
  Queries ~/claude-archive/sessions.db (msg + msg_fts) via sqlite3.exe.

.EXAMPLE
  .\csearch.ps1 ZyXEL
  .\csearch.ps1 '"auto-power-down"' network
  .\csearch.ps1 'Sophos AND SEDService' network

.NOTES
  Requires:
    - sqlite3.exe in PATH (e.g. winget install sqlite.sqlite)
    - ~/claude-archive/sessions.db populated by crs build
#>
param(
    [Parameter(Mandatory=$true,  Position=0)][string]$Query,
    [Parameter(Mandatory=$false, Position=1)][string]$Project = ""
)

$db = Join-Path $env:USERPROFILE "claude-archive\sessions.db"
if (-not (Test-Path $db)) {
    Write-Error "DB not found: $db. Run crs build first to ingest JSONLs."
    exit 1
}

$projFilter = if ($Project) { "AND project LIKE '%$Project%'" } else { "" }

# Escape single quotes in query for SQL safety
$qEscaped = $Query.Replace("'", "''")

$sql = @"
SELECT substr(session_id,1,8) AS session,
       substr(ts,1,19) AS ts,
       tool_name,
       substr(content,1,180) AS snippet
FROM msg
WHERE rowid IN (SELECT rowid FROM msg_fts WHERE content MATCH '$qEscaped')
  $projFilter
ORDER BY ts DESC
LIMIT 20
"@

& sqlite3.exe -column -header $db $sql
