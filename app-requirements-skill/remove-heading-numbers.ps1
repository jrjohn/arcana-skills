# ============================================================================
# remove-heading-numbers.ps1
# 移除 Markdown 檔案中標題的手動編號 (Windows PowerShell)
#
# 用途：確保 MD 檔案不含手動編號，以便 DOCX 轉換時正確自動編號
#
# 使用方式：
#   .\remove-heading-numbers.ps1 <input.md>
#   .\remove-heading-numbers.ps1 <input.md> <output.md>
#
# 範例：
#   .\remove-heading-numbers.ps1 SRS-Project-1.0.md
#   .\remove-heading-numbers.ps1 SRS-Project-1.0.md SRS-Project-cleaned.md
#
# 處理的編號格式：
#   ## 1. Introduction       -> ## Introduction
#   ### 1.1 Document Purpose -> ### Document Purpose
#   #### 1.1.1 Overview      -> #### Overview
#   ##### 1.1.1.1 Details    -> ##### Details
# ============================================================================

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$InputFile,

    [Parameter(Position=1)]
    [string]$OutputFile
)

# 設定輸出檔案
if (-not $OutputFile) {
    $OutputFile = $InputFile
}

# 檢查檔案是否存在
if (-not (Test-Path $InputFile)) {
    Write-Host "錯誤：找不到檔案 '$InputFile'" -ForegroundColor Red
    exit 1
}

# 建立備份
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupFile = "${InputFile}.backup.${Timestamp}"
Copy-Item $InputFile $BackupFile
Write-Host "已建立備份：$BackupFile" -ForegroundColor Yellow

# 讀取檔案內容
$Content = Get-Content $InputFile -Encoding UTF8

# 計算移除前的手動編號數量
$BeforeCount = ($Content | Select-String -Pattern '^#{1,6} [0-9]+\.' -AllMatches).Matches.Count

# 移除手動編號的正則表達式模式
$Patterns = @(
    '^(#{1,6}) ([0-9]+\.) ',
    '^(#{1,6}) ([0-9]+\.[0-9]+) ',
    '^(#{1,6}) ([0-9]+\.[0-9]+\.[0-9]+) ',
    '^(#{1,6}) ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+) ',
    '^(#{1,6}) ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+) '
)

# 處理每一行
$ProcessedContent = $Content | ForEach-Object {
    $line = $_
    foreach ($pattern in $Patterns) {
        $line = $line -replace $pattern, '$1 '
    }
    $line
}

# 寫入輸出檔案
$ProcessedContent | Set-Content $OutputFile -Encoding UTF8

# 計算移除後的手動編號數量
$AfterCount = ($ProcessedContent | Select-String -Pattern '^#{1,6} [0-9]+\.' -AllMatches).Matches.Count
$RemovedCount = $BeforeCount - $AfterCount

# 輸出結果
if ($RemovedCount -gt 0) {
    Write-Host "成功移除 $RemovedCount 個手動編號" -ForegroundColor Green
    Write-Host "輸出檔案：$OutputFile" -ForegroundColor Green
} else {
    Write-Host "檔案中沒有發現手動編號" -ForegroundColor Yellow
}

# 提示備份
if ($InputFile -eq $OutputFile) {
    Write-Host ""
    Write-Host "提示：備份檔案保留於 $BackupFile" -ForegroundColor Yellow
    Write-Host "如需刪除備份，請執行：Remove-Item `"$BackupFile`""
}

Write-Host ""
Write-Host "完成！"
