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
    "medical-software-requirements-skill"
)

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

    # Check Node.js (optional but recommended)
    $nodePath = Get-Command node -ErrorAction SilentlyContinue
    if (-not $nodePath) {
        Write-Warn "Node.js is not installed. Some skills may require it."
        Write-Info "Install from: https://nodejs.org/"
    }

    # Check Claude Code
    $claudePath = Get-Command claude -ErrorAction SilentlyContinue
    if (-not $claudePath) {
        Write-Warn "Claude Code CLI not found."
        Write-Info "Install: npm install -g @anthropic-ai/claude-code"
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

    git clone --depth 1 $RepoUrl $tempDir 2>$null

    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to clone repository"
        exit 1
    }

    return $tempDir
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

    # Check if skill already exists
    if (Test-Path $targetFull) {
        Write-Warn "Skill already exists: $SkillName"
        $response = Read-Host "  Overwrite? (y/N)"
        if ($response -notmatch '^[Yy]') {
            Write-Info "Skipping $SkillName"
            return
        }
        Remove-Item -Path $targetFull -Recurse -Force
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
        Remove-Item -Path $TempDir -Recurse -Force -ErrorAction SilentlyContinue
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

    if (Test-LocalRepo) {
        $sourcePath = $PSScriptRoot
        Write-Info "Using local repository"
    }
    else {
        $tempDir = Get-Repository
        $sourcePath = $tempDir
    }

    try {
        if ($All) {
            Install-AllSkills -SourcePath $sourcePath -TargetPath $skillsDir
        }
        else {
            Select-Skills -SourcePath $sourcePath -TargetPath $skillsDir
        }

        Show-Completion
    }
    finally {
        if ($tempDir) {
            Remove-TempFiles -TempDir $tempDir
        }
    }
}

# Run
Main
