<#
.SYNOPSIS
    iPad HTML -> iPhone HTML 轉換腳本 (PowerShell 版本)

.DESCRIPTION
    功能:
    - 保留模組子目錄結構 (iphone/auth/, iphone/vocab/, etc.)
    - 支援 CSS 變數替換 (--ipad-width → --iphone-width)
    - 支援硬編碼像素值替換 (1194px → 393px)
    - 自動更新導航連結

.EXAMPLE
    cd Z:\Documents\projects\{PROJECT}\04-ui-flow
    .\Convert-ToIphone.ps1

.EXAMPLE
    # 或使用完整路徑
    & "$env:USERPROFILE\.claude\skills\app-uiux-designer.skill\templates\ui-flow\scripts\Convert-ToIphone.ps1"

.NOTES
    Version: 2.0
    Author: app-uiux-designer.skill
#>

[CmdletBinding()]
param()

# 設定編碼
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     iPad → iPhone HTML 轉換工具 v2.0 (PowerShell)          ║" -ForegroundColor Cyan
Write-Host "║     保留模組子目錄結構 + CSS 變數支援                       ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# 確認當前目錄
if (-not (Test-Path "index.html")) {
    Write-Host "錯誤：請在 04-ui-flow 目錄下執行此腳本" -ForegroundColor Red
    Write-Host "用法: cd {PROJECT}\04-ui-flow; .\Convert-ToIphone.ps1"
    exit 1
}

# 自動偵測模組目錄
Write-Host "📁 偵測模組目錄..." -ForegroundColor Cyan

$excludeDirs = @("iphone", "docs", "shared", "workspace", "screenshots")
$modules = @()

Get-ChildItem -Directory | Where-Object {
    $_.Name -notin $excludeDirs
} | ForEach-Object {
    $dirName = $_.Name
    $screenFiles = Get-ChildItem -Path $_.FullName -Filter "SCR-*.html" -ErrorAction SilentlyContinue
    if ($screenFiles.Count -gt 0) {
        $modules += $dirName
        Write-Host "   ✓ $dirName ($($screenFiles.Count) 個畫面)" -ForegroundColor Green
    }
}

if ($modules.Count -eq 0) {
    Write-Host "錯誤：未找到任何模組目錄" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "📱 開始轉換..." -ForegroundColor Cyan
Write-Host ""

# 計數器
$totalConverted = 0
$totalErrors = 0

# 替換規則
$replacements = @(
    # CSS 變數替換
    @{ Pattern = 'width: var\(--ipad-width\);'; Replacement = 'width: var(--iphone-width);' },
    @{ Pattern = 'height: var\(--ipad-height\);'; Replacement = 'height: var(--iphone-height);' },
    # 硬編碼像素值替換
    @{ Pattern = 'width: 1194px;'; Replacement = 'width: 393px;' },
    @{ Pattern = 'height: 834px;'; Replacement = 'height: 852px;' },
    # viewport meta 替換
    @{ Pattern = 'width=1194, height=834'; Replacement = 'width=393, height=852' }
)

# 處理每個模組
foreach ($module in $modules) {
    # 創建 iPhone 模組目錄
    $iphoneModuleDir = "iphone\$module"
    if (-not (Test-Path $iphoneModuleDir)) {
        New-Item -ItemType Directory -Path $iphoneModuleDir -Force | Out-Null
    }

    $moduleCount = 0

    # 處理該模組下的所有 SCR-*.html 檔案
    Get-ChildItem -Path $module -Filter "SCR-*.html" | ForEach-Object {
        $ipadFile = $_.FullName
        $filename = $_.Name
        $iphoneFile = Join-Path $iphoneModuleDir $filename

        try {
            # 讀取檔案內容
            $content = Get-Content -Path $ipadFile -Raw -Encoding UTF8

            # 執行所有替換
            foreach ($rule in $replacements) {
                $content = $content -replace $rule.Pattern, $rule.Replacement
            }

            # 寫入 iPhone 版本
            $content | Set-Content -Path $iphoneFile -Encoding UTF8 -NoNewline

            $moduleCount++
            $script:totalConverted++
        }
        catch {
            Write-Host "  ✗ $filename ($($_.Exception.Message))" -ForegroundColor Red
            $script:totalErrors++
        }
    }

    Write-Host "   ✓ ${module}: $moduleCount 個檔案" -ForegroundColor Green
}

Write-Host ""
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor White
Write-Host "📊 轉換結果" -ForegroundColor White -NoNewline
Write-Host ""
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor White

# 統計
$ipadCount = (Get-ChildItem -Path . -Filter "SCR-*.html" -Recurse |
    Where-Object { $_.FullName -notmatch "\\iphone\\" -and $_.FullName -notmatch "\\docs\\" }).Count
$iphoneCount = (Get-ChildItem -Path ".\iphone" -Filter "SCR-*.html" -Recurse -ErrorAction SilentlyContinue).Count

Write-Host "   iPad 畫面:   $ipadCount"
Write-Host "   iPhone 畫面: $iphoneCount"
Write-Host "   轉換成功:    $totalConverted"
Write-Host "   轉換失敗:    $totalErrors"
Write-Host ""

# 驗證
if ($iphoneCount -eq $ipadCount) {
    Write-Host "✅ 驗證通過：iPad ($ipadCount) = iPhone ($iphoneCount)" -ForegroundColor Green
}
else {
    Write-Host "⚠️  警告：iPad ($ipadCount) != iPhone ($iphoneCount)" -ForegroundColor Yellow
}

# 抽樣檢查
Write-Host ""
Write-Host "🔍 抽樣檢查..." -ForegroundColor Cyan

$sampleFile = Get-ChildItem -Path ".\iphone" -Filter "SCR-*.html" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
if ($sampleFile) {
    $sampleContent = Get-Content -Path $sampleFile.FullName -Raw

    if ($sampleContent -match "var\(--iphone-width\)") {
        Write-Host "   ✓ CSS 變數已正確替換" -ForegroundColor Green
    }
    elseif ($sampleContent -match "width: 393px") {
        Write-Host "   ✓ 硬編碼像素值已正確替換" -ForegroundColor Green
    }
    else {
        Write-Host "   ⚠ 尺寸替換可能未生效，請手動檢查" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor White
Write-Host "✅ 轉換完成！" -ForegroundColor Green
Write-Host ""
Write-Host "下一步:"
Write-Host "  1. 執行驗證腳本確認導航連結"
Write-Host "  2. 更新 ui-flow-diagram-iphone.html"
Write-Host "  3. 更新 device-preview.html 側邊欄"
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor White
