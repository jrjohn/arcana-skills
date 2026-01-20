# doc-indexer-skill 安裝腳本 (Windows)
# 用法: PowerShell -ExecutionPolicy Bypass -File setup.ps1

param(
    [switch]$Force,
    [string]$InstallDir = "$env:LOCALAPPDATA\doc-indexer"
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  doc-indexer-skill 安裝程式" -ForegroundColor Cyan
Write-Host "  平台: Windows" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 設定變數
$SkillDir = "$env:USERPROFILE\.claude\skills\doc-indexer-skill"
$JarName = "doc-indexer-1.0.0-all.jar"
$JarUrl = "https://github.com/jrjohn/arcana-skills/releases/latest/download/$JarName"
$JavaMinVersion = 17

# 函數: 檢查 Java 版本
function Get-JavaVersion {
    try {
        $javaOutput = & java -version 2>&1 | Select-Object -First 1
        if ($javaOutput -match '"(\d+)') {
            return [int]$Matches[1]
        }
    } catch {
        return 0
    }
    return 0
}

# 函數: 安裝 Java (使用 winget)
function Install-Java {
    Write-Host "正在安裝 Java $JavaMinVersion..." -ForegroundColor Yellow

    # 檢查 winget 是否可用
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        try {
            winget install Microsoft.OpenJDK.$JavaMinVersion --silent --accept-package-agreements --accept-source-agreements
            Write-Host "✓ Java $JavaMinVersion 安裝完成" -ForegroundColor Green

            # 重新載入環境變數
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

            return $true
        } catch {
            Write-Host "winget 安裝失敗: $_" -ForegroundColor Red
        }
    }

    # 嘗試 Chocolatey
    if (Get-Command choco -ErrorAction SilentlyContinue) {
        try {
            choco install openjdk$JavaMinVersion -y
            Write-Host "✓ Java $JavaMinVersion 安裝完成 (via Chocolatey)" -ForegroundColor Green
            return $true
        } catch {
            Write-Host "Chocolatey 安裝失敗: $_" -ForegroundColor Red
        }
    }

    Write-Host "無法自動安裝 Java，請手動下載安裝:" -ForegroundColor Red
    Write-Host "  https://adoptium.net/temurin/releases/?version=$JavaMinVersion" -ForegroundColor Yellow
    return $false
}

# 函數: 找到 JAVA_HOME
function Find-JavaHome {
    # 優先使用環境變數
    if ($env:JAVA_HOME -and (Test-Path "$env:JAVA_HOME\bin\java.exe")) {
        return $env:JAVA_HOME
    }

    # 搜尋常見位置
    $searchPaths = @(
        "$env:ProgramFiles\Eclipse Adoptium\jdk-*",
        "$env:ProgramFiles\Microsoft\jdk-*",
        "$env:ProgramFiles\Java\jdk-*",
        "$env:ProgramFiles\OpenJDK\jdk-*"
    )

    foreach ($pattern in $searchPaths) {
        $found = Get-ChildItem -Path $pattern -Directory -ErrorAction SilentlyContinue |
                 Sort-Object Name -Descending |
                 Select-Object -First 1

        if ($found -and (Test-Path "$($found.FullName)\bin\java.exe")) {
            return $found.FullName
        }
    }

    # 從 PATH 中找
    $javaExe = Get-Command java -ErrorAction SilentlyContinue
    if ($javaExe) {
        $javaPath = Split-Path (Split-Path $javaExe.Source -Parent) -Parent
        return $javaPath
    }

    return $null
}

# 步驟 1: 檢查/安裝 Java
Write-Host "步驟 1/4: 檢查 Java 環境..." -ForegroundColor White
$javaVersion = Get-JavaVersion

if ($javaVersion -lt $JavaMinVersion) {
    Write-Host "Java 版本不足 (目前: $javaVersion, 需要: $JavaMinVersion)" -ForegroundColor Yellow

    $response = Read-Host "是否自動安裝 Java $JavaMinVersion? (y/n)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        if (-not (Install-Java)) {
            exit 1
        }
    } else {
        Write-Host "請手動安裝 Java $JavaMinVersion 後重新執行此腳本" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✓ Java $javaVersion 已安裝" -ForegroundColor Green
}

# 步驟 2: 建立安裝目錄
Write-Host ""
Write-Host "步驟 2/4: 建立安裝目錄..." -ForegroundColor White

if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}
Write-Host "✓ 安裝目錄: $InstallDir" -ForegroundColor Green

# 步驟 3: 下載 JAR
Write-Host ""
Write-Host "步驟 3/4: 下載 doc-indexer..." -ForegroundColor White

$JarPath = Join-Path $InstallDir $JarName

if ((Test-Path $JarPath) -and -not $Force) {
    $response = Read-Host "JAR 檔案已存在，是否重新下載? (y/n)"
    if ($response -ne 'y' -and $response -ne 'Y') {
        Write-Host "跳過下載" -ForegroundColor Yellow
    } else {
        Remove-Item $JarPath -Force
    }
}

if (-not (Test-Path $JarPath)) {
    Write-Host "從 GitHub 下載..." -ForegroundColor White
    try {
        Invoke-WebRequest -Uri $JarUrl -OutFile $JarPath -UseBasicParsing
        Write-Host "✓ 下載完成" -ForegroundColor Green
    } catch {
        Write-Host "GitHub 下載失敗，嘗試從原始碼建置..." -ForegroundColor Yellow

        $SourceDir = "$SkillDir\source"
        if ((Test-Path $SourceDir) -and (Test-Path "$SourceDir\gradlew.bat")) {
            Write-Host "從原始碼建置中..." -ForegroundColor White
            Push-Location $SourceDir
            try {
                & .\gradlew.bat shadowJar --no-daemon
                $SourceJar = "$SourceDir\build\libs\$JarName"
                if (Test-Path $SourceJar) {
                    Copy-Item $SourceJar $JarPath
                    Write-Host "✓ 從原始碼建置完成" -ForegroundColor Green
                }
            } catch {
                Write-Host "建置失敗: $_" -ForegroundColor Red
            }
            Pop-Location
        } else {
            Write-Host "無法找到原始碼，請手動下載 JAR" -ForegroundColor Red
            Write-Host ""
            Write-Host "手動下載步驟:" -ForegroundColor Cyan
            Write-Host "1. 前往 https://github.com/jrjohn/arcana-skills/releases"
            Write-Host "2. 下載 $JarName"
            Write-Host "3. 將檔案複製到 $InstallDir"
        }
    }
}

# 步驟 4: 產生設定檔
Write-Host ""
Write-Host "步驟 4/4: 產生設定檔..." -ForegroundColor White

$JavaHome = Find-JavaHome

if (-not $JavaHome) {
    Write-Host "警告: 無法自動偵測 JAVA_HOME，請手動設定" -ForegroundColor Yellow
    $JavaHome = "C:\Program Files\Microsoft\jdk-$JavaMinVersion"
}

# 建立 skill 目錄
if (-not (Test-Path $SkillDir)) {
    New-Item -ItemType Directory -Path $SkillDir -Force | Out-Null
}

$ConfigFile = Join-Path $SkillDir "config.env"
$ConfigContent = @"
# doc-indexer-skill 設定檔
# 自動產生於: $(Get-Date)
# 平台: Windows

JAVA_HOME=$JavaHome
DOC_INDEXER_JAR=$JarPath
DOC_INDEXER_INDEX=$env:LOCALAPPDATA\doc-indexer\index-data
"@

$ConfigContent | Out-File -FilePath $ConfigFile -Encoding UTF8
Write-Host "✓ 設定檔已產生: $ConfigFile" -ForegroundColor Green

# 完成
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  安裝完成!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "設定資訊:" -ForegroundColor White
Write-Host "  JAVA_HOME: $JavaHome"
Write-Host "  JAR 位置:  $JarPath"
Write-Host "  設定檔:    $ConfigFile"
Write-Host ""
Write-Host "使用方式:" -ForegroundColor White
Write-Host '  /doc-indexer search "關鍵字"'
Write-Host '  /doc-indexer index "C:\path\to\docs"'
Write-Host ""
