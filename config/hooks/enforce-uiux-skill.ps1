#
# Enforce UI/UX Designer Skill Hook (Windows PowerShell)
# Triggered after Write|Edit operations on SDD files
# Reminds to use app-uiux-designer.skill for UI Flow generation
#

# Read hook input from stdin (Claude Code passes JSON via stdin)
try {
    $InputJson = $input | Out-String
    if ($InputJson) {
        $HookData = $InputJson | ConvertFrom-Json -ErrorAction SilentlyContinue
        $FilePath = $HookData.tool_input.file_path
    }
} catch {
    $FilePath = $null
}

# Only check SDD files
if (-not $FilePath) { exit 0 }
if ($FilePath -notmatch 'SDD.*\.md$') { exit 0 }

# Check if this is a new SDD or significant update
if (Test-Path $FilePath) {
    $Content = Get-Content $FilePath -Raw -ErrorAction SilentlyContinue

    # Check if SDD has screen designs section
    if ($Content -match '## Screen Designs|## Design Views|SCR-') {
        Write-Output ""
        Write-Output "========================================"
        Write-Output "[REMINDER] SDD with screen designs detected!"
        Write-Output "----------------------------------------"
        Write-Output "According to IEC 62304 workflow:"
        Write-Output "  1. Use 'app-uiux-designer.skill' to generate UI Flow"
        Write-Output "  2. Generate Design Tokens + Theme CSS"
        Write-Output "  3. Create HTML UI Flow prototype"
        Write-Output "  4. Capture screenshots"
        Write-Output "  5. Update SDD with UI references"
        Write-Output "  6. Update SRS with Screen References"
        Write-Output "========================================"
        Write-Output ""
    }
}

exit 0
