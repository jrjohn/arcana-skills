#
# Claude Code Status Line Command (Windows PowerShell)
# Shows project context and git status
#

# Get current directory name
$ProjectName = Split-Path -Leaf (Get-Location)

# Get git branch if in a git repo
$GitBranch = ""
try {
    $null = git rev-parse --git-dir 2>$null
    if ($LASTEXITCODE -eq 0) {
        $GitBranch = git branch --show-current 2>$null
        if ($GitBranch) {
            $GitBranch = " [$GitBranch]"
        }
    }
} catch {}

# Get number of modified files
$ModifiedCount = ""
try {
    $null = git rev-parse --git-dir 2>$null
    if ($LASTEXITCODE -eq 0) {
        $Count = (git status --porcelain 2>$null | Measure-Object -Line).Lines
        if ($Count -gt 0) {
            $ModifiedCount = " (+$Count)"
        }
    }
} catch {}

# Output status line
Write-Output "${ProjectName}${GitBranch}${ModifiedCount}"
