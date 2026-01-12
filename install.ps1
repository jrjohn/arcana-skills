#Requires -Version 5.1
<#
.SYNOPSIS
    Arcana Skills Installer for Claude Code (Windows)

.DESCRIPTION
    Installs Arcana Skills for Claude Code on Windows (Native or WSL2)

.PARAMETER All
    Install all skills without prompting

.PARAMETER WSL
    Install to WSL2 environment instead of native Windows

.EXAMPLE
    # Interactive installation
    .\install.ps1

.EXAMPLE
    # Install all skills
    .\install.ps1 -All

.EXAMPLE
    # Install to WSL2
    .\install.ps1 -WSL

.EXAMPLE
    # Remote execution
    iwr -useb https://raw.githubusercontent.com/jrjohn/arcana-skills/main/install.ps1 | iex
#>

param(
    [switch]$All,
    [switch]$WSL,
    [switch]$Help
)

# Configuration
$RepoUrl = "https://github.com/jrjohn/arcana-skills.git"
$Skills = @(
    "ios-developer-skill"
    "android-developer-skill"
    "react-developer-skill"
    "angular-developer-skill"
    "nodejs-developer-skill"
    "python-developer-skill"
    "springboot-developer-skill"
    "windows-developer-skill"
    "app-requirements-skill"
    "app-uiux-designer.skill"
)

# Config paths
$ClaudeDir = Join-Path $env:USERPROFILE ".claude"
$UserSettings = Join-Path $ClaudeDir "settings.json"
$UserClaudeMd = Join-Path $ClaudeDir "CLAUDE.md"
$HooksDir = Join-Path $ClaudeDir "hooks"

# Colors
function Write-Color {
    param(
        [string]$Text,
        [string]$Color = "White"
    )
    Write-Host $Text -ForegroundColor $Color
}

function Write-Info { Write-Color "[INFO] $args" "Cyan" }
function Write-Success { Write-Color "[SUCCESS] $args" "Green" }
function Write-Warn { Write-Color "[WARN] $args" "Yellow" }
function Write-Error { Write-Color "[ERROR] $args" "Red" }

# Print banner
function Show-Banner {
    Write-Host ""
    Write-Color "================================================================" "Blue"
    Write-Color "                                                                " "Blue"
    Write-Color "              Arcana Skills Installer                           " "Blue"
    Write-Color "              for Claude Code (Windows)                         " "Blue"
    Write-Color "                                                                " "Blue"
    Write-Color "================================================================" "Blue"
    Write-Host ""
}

# Show help
function Show-Help {
    Write-Host @"
Arcana Skills Installer for Claude Code (Windows)

Usage: .\install.ps1 [OPTIONS]

Options:
  -All      Install all skills without prompting
  -WSL      Install to WSL2 environment
  -Help     Show this help message

Examples:
  .\install.ps1           # Interactive installation
  .\install.ps1 -All      # Install all skills
  .\install.ps1 -WSL      # Install to WSL2
  .\install.ps1 -WSL -All # Install all to WSL2
"@
}

# Check if running in WSL
function Test-WSLAvailable {
    try {
        $wslList = wsl --list --quiet 2>$null
        return $LASTEXITCODE -eq 0
    }
    catch {
        return $false
    }
}

# Install via WSL
function Install-ViaWSL {
    param([bool]$InstallAll)

    Write-Info "Detecting WSL2 distributions..."

    if (-not (Test-WSLAvailable)) {
        Write-Error "WSL2 is not installed or not available."
        Write-Info "To install WSL2, run: wsl --install"
        exit 1
    }

    # Get default WSL distribution
    $defaultDistro = wsl --list --quiet 2>$null | Select-Object -First 1
    if ([string]::IsNullOrEmpty($defaultDistro)) {
        Write-Error "No WSL distribution found."
        Write-Info "Install a distribution: wsl --install -d Ubuntu"
        exit 1
    }

    Write-Info "Using WSL distribution: $defaultDistro"

    # Download and run install.sh in WSL
    $installCmd = "curl -fsSL https://raw.githubusercontent.com/jrjohn/arcana-skills/main/install.sh | bash"
    if ($InstallAll) {
        $installCmd = "curl -fsSL https://raw.githubusercontent.com/jrjohn/arcana-skills/main/install.sh | bash -s -- --all"
    }

    Write-Info "Running installer in WSL..."
    wsl bash -c $installCmd

    if ($LASTEXITCODE -eq 0) {
        Write-Success "Installation completed in WSL2!"
    }
    else {
        Write-Error "Installation failed in WSL2."
        exit 1
    }
}

# Install Node.js
function Install-NodeJS {
    Write-Info "Installing Node.js..."

    # Check if winget is available
    $wingetPath = Get-Command winget -ErrorAction SilentlyContinue
    if ($wingetPath) {
        Write-Info "Using winget to install Node.js..."
        winget install OpenJS.NodeJS.LTS --accept-package-agreements --accept-source-agreements
    }
    # Check if choco is available
    elseif (Get-Command choco -ErrorAction SilentlyContinue) {
        Write-Info "Using Chocolatey to install Node.js..."
        choco install nodejs-lts -y
    }
    else {
        Write-Error "No package manager found (winget or choco)."
        Write-Info "Please install Node.js manually from: https://nodejs.org/"
        Write-Info "Or install winget: https://aka.ms/getwinget"
        exit 1
    }

    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

    # Verify installation
    $nodePath = Get-Command node -ErrorAction SilentlyContinue
    if ($nodePath) {
        $nodeVersion = node --version
        Write-Success "Node.js installed successfully: $nodeVersion"
    }
    else {
        Write-Error "Node.js installation failed."
        Write-Info "Please restart your terminal and try again."
        exit 1
    }
}

# Install Claude Code CLI
function Install-ClaudeCLI {
    Write-Info "Installing Claude Code CLI..."

    npm install -g @anthropic-ai/claude-code

    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

    # Verify installation
    $claudePath = Get-Command claude -ErrorAction SilentlyContinue
    if ($claudePath) {
        Write-Success "Claude Code CLI installed successfully"
    }
    else {
        Write-Error "Claude Code CLI installation failed."
        Write-Info "Try running as Administrator: npm install -g @anthropic-ai/claude-code"
        exit 1
    }
}

# Check prerequisites
function Test-Prerequisites {
    Write-Info "Checking prerequisites..."

    # Check git
    $gitPath = Get-Command git -ErrorAction SilentlyContinue
    if (-not $gitPath) {
        Write-Error "git is not installed."
        Write-Info "Install git from: https://git-scm.com/download/win"
        Write-Info "Or via winget: winget install Git.Git"
        exit 1
    }

    # Check Node.js (required)
    $nodePath = Get-Command node -ErrorAction SilentlyContinue
    if (-not $nodePath) {
        Write-Warn "Node.js is not installed."
        $response = Read-Host "  Install Node.js automatically? (Y/n)"
        if ($response -notmatch '^[Nn]') {
            Install-NodeJS
        }
        else {
            Write-Error "Node.js is required. Please install it manually."
            Write-Info "Install from: https://nodejs.org/"
            exit 1
        }
    }

    # Check Claude Code (required)
    $claudePath = Get-Command claude -ErrorAction SilentlyContinue
    if (-not $claudePath) {
        Write-Warn "Claude Code CLI not found."
        $response = Read-Host "  Install Claude Code CLI automatically? (Y/n)"
        if ($response -notmatch '^[Nn]') {
            Install-ClaudeCLI
        }
        else {
            Write-Error "Claude Code CLI is required. Please install it manually."
            Write-Info "Install: npm install -g @anthropic-ai/claude-code"
            exit 1
        }
    }

    Write-Success "Prerequisites check passed"
}

# Get skills directory
function Get-SkillsDir {
    $userProfile = $env:USERPROFILE
    $skillsDir = Join-Path $userProfile ".claude\skills"
    return $skillsDir
}

# Ensure skills directory exists
function Initialize-SkillsDir {
    $skillsDir = Get-SkillsDir
    if (-not (Test-Path $skillsDir)) {
        Write-Info "Creating skills directory: $skillsDir"
        New-Item -ItemType Directory -Path $skillsDir -Force | Out-Null
    }
    return $skillsDir
}

# Detect if running from cloned repo
function Test-LocalRepo {
    $scriptPath = $PSScriptRoot
    if ([string]::IsNullOrEmpty($scriptPath)) {
        # Running from remote (iex)
        return $false
    }
    $testFile = Join-Path $scriptPath "ios-developer-skill\SKILL.md"
    return Test-Path $testFile
}

# Clone repository
function Get-Repository {
    $tempDir = Join-Path $env:TEMP "arcana-skills-$(Get-Random)"
    Write-Info "Cloning repository..."

    # Clone with visible output so users can see any errors
    $gitOutput = git clone --depth 1 $RepoUrl $tempDir 2>&1

    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to clone repository"
        Write-Host ""
        Write-Host "Git output:" -ForegroundColor Yellow
        Write-Host $gitOutput
        Write-Host ""
        Write-Info "Troubleshooting:"
        Write-Host "  1. Check your internet connection"
        Write-Host "  2. Verify git is working: git --version"
        Write-Host "  3. Try cloning manually: git clone $RepoUrl"
        Write-Host "  4. If behind a proxy, configure git proxy settings"
        Write-Host ""
        # Use throw to ensure proper error propagation
        throw "Repository clone failed"
    }

    return $tempDir
}

# Remove directory robustly (handles Windows reserved names like nul, con, etc.)
function Remove-DirectoryRobust {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        return $true
    }

    # First try normal removal
    try {
        Remove-Item -Path $Path -Recurse -Force -ErrorAction Stop
        return $true
    }
    catch {
        # If failed, try cmd.exe rd command which handles some edge cases better
        try {
            $cmdResult = cmd.exe /c "rd /s /q `"$Path`"" 2>&1
            if (-not (Test-Path $Path)) {
                return $true
            }
        }
        catch { }

        # Try robocopy trick - mirror an empty folder to delete everything
        try {
            $emptyDir = Join-Path $env:TEMP "empty-$(Get-Random)"
            New-Item -ItemType Directory -Path $emptyDir -Force | Out-Null
            $robocopyResult = robocopy $emptyDir $Path /MIR /NFL /NDL /NJH /NJS /nc /ns /np 2>$null
            Remove-Item -Path $emptyDir -Force -ErrorAction SilentlyContinue

            # Now try to remove the empty directory
            if (Test-Path $Path) {
                Remove-Item -Path $Path -Force -ErrorAction SilentlyContinue
            }

            if (-not (Test-Path $Path)) {
                return $true
            }
        }
        catch { }

        # Last resort: use \\?\ prefix to delete reserved names via cmd.exe
        try {
            # Convert path to \\?\ format for handling reserved names
            $longPath = "\\?\$Path"
            # Find and delete files with reserved names first
            Get-ChildItem -Path $Path -Recurse -Force -ErrorAction SilentlyContinue | ForEach-Object {
                $itemPath = $_.FullName
                $itemLongPath = "\\?\$itemPath"
                if ($_.PSIsContainer) {
                    cmd.exe /c "rd /s /q `"$itemLongPath`"" 2>$null
                } else {
                    cmd.exe /c "del /f /q `"$itemLongPath`"" 2>$null
                }
            }
            # Try to remove the main directory
            cmd.exe /c "rd /s /q `"$longPath`"" 2>$null

            if (-not (Test-Path $Path)) {
                return $true
            }
        }
        catch { }

        Write-Warn "Could not completely remove $Path - some files may remain"
        return $false
    }
}

# Install a single skill
function Install-Skill {
    param(
        [string]$SkillName,
        [string]$SourcePath,
        [string]$TargetPath
    )

    $sourceFull = Join-Path $SourcePath $SkillName
    $targetFull = Join-Path $TargetPath $SkillName

    if (-not (Test-Path $sourceFull)) {
        Write-Warn "Skill not found: $SkillName (skipping)"
        return
    }

    # Auto-remove old skill if exists (for clean reinstall)
    if (Test-Path $targetFull) {
        Write-Info "Removing old version: $SkillName"
        Remove-DirectoryRobust -Path $targetFull | Out-Null
    }

    Write-Info "Installing: $SkillName"

    # Copy skill (excluding unnecessary files)
    $excludePatterns = @('node_modules', '.git', '.DS_Store', '*.log')

    # Create target directory
    New-Item -ItemType Directory -Path $targetFull -Force | Out-Null

    # Copy files with exclusions
    Get-ChildItem -Path $sourceFull -Recurse | ForEach-Object {
        $relativePath = $_.FullName.Substring($sourceFull.Length + 1)
        $shouldExclude = $false

        foreach ($pattern in $excludePatterns) {
            if ($relativePath -like "*$pattern*") {
                $shouldExclude = $true
                break
            }
        }

        if (-not $shouldExclude) {
            $targetFile = Join-Path $targetFull $relativePath
            if ($_.PSIsContainer) {
                New-Item -ItemType Directory -Path $targetFile -Force -ErrorAction SilentlyContinue | Out-Null
            }
            else {
                $targetDir = Split-Path $targetFile -Parent
                if (-not (Test-Path $targetDir)) {
                    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
                }
                Copy-Item -Path $_.FullName -Destination $targetFile -Force
            }
        }
    }

    # Install npm dependencies if package.json exists
    $packageJson = Join-Path $targetFull "package.json"
    if (Test-Path $packageJson) {
        Write-Info "  Installing npm dependencies for $SkillName..."
        Push-Location $targetFull
        try {
            npm install --silent 2>$null
        }
        catch {
            Write-Warn "  Failed to install npm dependencies (npm may not be installed)"
        }
        Pop-Location
    }

    Write-Success "Installed: $SkillName"
}

# Install all skills
function Install-AllSkills {
    param(
        [string]$SourcePath,
        [string]$TargetPath
    )

    Write-Info "Installing $($Skills.Count) skills..."
    Write-Host ""

    foreach ($skill in $Skills) {
        Install-Skill -SkillName $skill -SourcePath $SourcePath -TargetPath $TargetPath
    }
}

# Interactive skill selection
function Select-Skills {
    param(
        [string]$SourcePath,
        [string]$TargetPath
    )

    Write-Host ""
    Write-Info "Available skills:"
    Write-Host ""

    for ($i = 0; $i -lt $Skills.Count; $i++) {
        Write-Host "  $($i + 1)) $($Skills[$i])"
    }

    Write-Host ""
    Write-Host "  a) Install all skills"
    Write-Host "  q) Quit"
    Write-Host ""

    $selection = Read-Host "Enter skill numbers (comma-separated) or 'a' for all"

    if ($selection -eq 'q') {
        Write-Info "Installation cancelled"
        exit 0
    }

    if ($selection -eq 'a') {
        Install-AllSkills -SourcePath $SourcePath -TargetPath $TargetPath
        return
    }

    # Parse comma-separated selection
    $indices = $selection -split ',' | ForEach-Object { $_.Trim() }
    foreach ($idx in $indices) {
        if ($idx -match '^\d+$') {
            $num = [int]$idx
            if ($num -ge 1 -and $num -le $Skills.Count) {
                Install-Skill -SkillName $Skills[$num - 1] -SourcePath $SourcePath -TargetPath $TargetPath
            }
            else {
                Write-Warn "Invalid selection: $idx"
            }
        }
        else {
            Write-Warn "Invalid selection: $idx"
        }
    }
}

# Generate skill permissions for settings
function Get-SkillPermissions {
    $permissions = @()
    foreach ($skill in $Skills) {
        $permissions += "Skill($skill)"
    }
    return $permissions
}

# Merge settings.json
function Merge-Settings {
    param([string]$SourcePath)

    $templateSettings = Join-Path $SourcePath "config\settings.template.windows.json"

    if (-not (Test-Path $templateSettings)) {
        Write-Warn "settings.template.windows.json not found, skipping settings merge"
        return
    }

    Write-Info "Merging settings.json..."

    # Read template
    $template = Get-Content $templateSettings -Raw | ConvertFrom-Json

    # Add dynamic skill permissions
    $skillPerms = Get-SkillPermissions
    $template.permissions.allow += $skillPerms
    $template.permissions.allow = $template.permissions.allow | Select-Object -Unique

    # Create or merge user settings
    if (-not (Test-Path $UserSettings)) {
        Write-Info "  Creating new settings.json"
        $template | ConvertTo-Json -Depth 10 | Set-Content $UserSettings -Encoding UTF8
        Write-Success "Settings configured"
        return
    }

    # Backup existing settings
    $backupPath = "$UserSettings.backup"
    Copy-Item $UserSettings $backupPath -Force
    Write-Info "  Backed up existing settings to settings.json.backup"

    # Read existing settings and merge
    try {
        $existing = Get-Content $UserSettings -Raw | ConvertFrom-Json

        # Merge permissions (add new ones)
        if ($existing.permissions -and $existing.permissions.allow) {
            $merged = $existing.permissions.allow + $template.permissions.allow | Select-Object -Unique
            $existing.permissions.allow = $merged
        } else {
            $existing | Add-Member -NotePropertyName "permissions" -NotePropertyValue $template.permissions -Force
        }

        # Add other settings if not present
        if (-not $existing.statusLine) {
            $existing | Add-Member -NotePropertyName "statusLine" -NotePropertyValue $template.statusLine -Force
        }
        if (-not $existing.hooks) {
            $existing | Add-Member -NotePropertyName "hooks" -NotePropertyValue $template.hooks -Force
        }
        if (-not $existing.enabledPlugins) {
            $existing | Add-Member -NotePropertyName "enabledPlugins" -NotePropertyValue $template.enabledPlugins -Force
        }

        $existing | ConvertTo-Json -Depth 10 | Set-Content $UserSettings -Encoding UTF8
        Write-Success "Settings merged successfully"
    }
    catch {
        Write-Warn "Settings merge failed, restoring backup"
        Copy-Item $backupPath $UserSettings -Force
    }
}

# Merge CLAUDE.md
function Merge-ClaudeMd {
    param([string]$SourcePath)

    $templateClaudeMd = Join-Path $SourcePath "config\CLAUDE.template.md"
    $marker = "# Arcana Skills Configuration"

    if (-not (Test-Path $templateClaudeMd)) {
        Write-Warn "CLAUDE.template.md not found, skipping CLAUDE.md merge"
        return
    }

    Write-Info "Configuring CLAUDE.md..."

    # Create if not exists
    if (-not (Test-Path $UserClaudeMd)) {
        Write-Info "  Creating new CLAUDE.md"
        Copy-Item $templateClaudeMd $UserClaudeMd
        Write-Success "CLAUDE.md configured"
        return
    }

    # Check if already contains our config
    $content = Get-Content $UserClaudeMd -Raw
    if ($content -match [regex]::Escape($marker)) {
        Write-Info "  CLAUDE.md already contains Arcana Skills config"
        Write-Info "  Keeping existing config"
        return
    }

    # Append template
    $templateContent = Get-Content $templateClaudeMd -Raw
    Add-Content $UserClaudeMd "`n$templateContent"
    Write-Success "CLAUDE.md updated"
}

# Install hooks
function Install-Hooks {
    param([string]$SourcePath)

    $hooksSource = Join-Path $SourcePath "config\hooks"

    if (-not (Test-Path $hooksSource)) {
        return
    }

    Write-Info "Installing hooks..."

    # Create hooks directory
    if (-not (Test-Path $HooksDir)) {
        New-Item -ItemType Directory -Path $HooksDir -Force | Out-Null
    }

    # Copy PowerShell hook scripts
    Get-ChildItem -Path $hooksSource -Filter "*.ps1" | ForEach-Object {
        $targetPath = Join-Path $HooksDir $_.Name
        Copy-Item $_.FullName $targetPath -Force
        Write-Info "  Installed hook: $($_.Name)"
    }

    # Copy statusline script
    $statuslineSource = Join-Path $SourcePath "config\statusline-command.ps1"
    if (Test-Path $statuslineSource) {
        $statuslineTarget = Join-Path $ClaudeDir "statusline-command.ps1"
        Copy-Item $statuslineSource $statuslineTarget -Force
        Write-Info "  Installed statusline command"
    }

    Write-Success "Hooks installed"
}

# Print completion message
function Show-Completion {
    $skillsDir = Get-SkillsDir

    Write-Host ""
    Write-Color "================================================================" "Green"
    Write-Color "                                                                " "Green"
    Write-Color "              Installation Complete!                            " "Green"
    Write-Color "                                                                " "Green"
    Write-Color "================================================================" "Green"
    Write-Host ""
    Write-Info "Skills installed to: $skillsDir"
    Write-Host ""
    Write-Info "To verify installation, run Claude Code and ask:"
    Write-Host "  'What Skills are available?'"
    Write-Host ""
}

# Cleanup
function Remove-TempFiles {
    param([string]$TempDir)

    if ($TempDir -and (Test-Path $TempDir)) {
        Remove-DirectoryRobust -Path $TempDir | Out-Null
    }
}

# Main
function Main {
    if ($Help) {
        Show-Help
        return
    }

    Show-Banner

    # WSL mode
    if ($WSL) {
        Install-ViaWSL -InstallAll $All
        return
    }

    # Native Windows installation
    Test-Prerequisites
    $skillsDir = Initialize-SkillsDir

    # Determine source
    $sourcePath = $null
    $tempDir = $null

    try {
        if (Test-LocalRepo) {
            $sourcePath = $PSScriptRoot
            Write-Info "Using local repository"
        }
        else {
            $tempDir = Get-Repository
            $sourcePath = $tempDir
        }

        if ($All) {
            Install-AllSkills -SourcePath $sourcePath -TargetPath $skillsDir
        }
        else {
            Select-Skills -SourcePath $sourcePath -TargetPath $skillsDir
        }

        # Configure settings and hooks
        Write-Host ""
        Write-Info "Configuring Claude Code settings..."
        Merge-Settings -SourcePath $sourcePath
        Merge-ClaudeMd -SourcePath $sourcePath
        Install-Hooks -SourcePath $sourcePath

        Show-Completion
    }
    catch {
        Write-Error $_.Exception.Message
        exit 1
    }
    finally {
        if ($tempDir) {
            Remove-TempFiles -TempDir $tempDir
        }
    }
}

# Run
try {
    Main
}
catch {
    Write-Color "[ERROR] $($_.Exception.Message)" "Red"
    exit 1
}
