#
# Validate UI Flow Hook (Windows PowerShell)
# Triggered after Write|Edit operations on files
# Validates HTML UI Flow files for common issues
#

# Get the file path from environment (set by Claude Code hooks)
$FilePath = $env:CLAUDE_FILE_PATH

# Only validate UI Flow HTML files
if (-not $FilePath) { exit 0 }
if ($FilePath -notmatch '\.html$') { exit 0 }
if ($FilePath -notmatch '(ui-flow|uiflow|screen)') { exit 0 }

# Check if file exists
if (-not (Test-Path $FilePath)) { exit 0 }

# Validation checks
$Errors = @()
$Content = Get-Content $FilePath -Raw -ErrorAction SilentlyContinue

if ($Content) {
    # Check for empty href attributes (navigation issues)
    if ($Content -match 'href=""') {
        $Errors += "Empty href attributes found - navigation links may be broken"
    }

    # Check for missing screen IDs
    if ($Content -match 'id=""') {
        $Errors += "Empty id attributes found - screen references may be incomplete"
    }

    # Check for TODO markers
    if ($Content -match '(?i)(TODO|FIXME|XXX)') {
        $Errors += "TODO/FIXME markers found - review before finalizing"
    }

    # Check for placeholder images
    if ($Content -match 'src="(placeholder|TODO|)"') {
        $Errors += "Placeholder or empty image sources found"
    }
}

# Output validation results
if ($Errors.Count -gt 0) {
    Write-Output "UI Flow Validation Warnings:"
    foreach ($error in $Errors) {
        Write-Output "  - $error"
    }
}

exit 0
