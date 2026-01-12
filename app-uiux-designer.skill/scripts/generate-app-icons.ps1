# ============================================
# App Icon Generator for iOS & Android (Windows)
# ============================================
# 從 1024x1024 PNG/SVG 來源產生所有平台 app icon 尺寸
#
# 使用方式:
#   .\generate-app-icons.ps1 [source_image] [output_dir]
#
# 參數:
#   source_image - PNG (1024x1024) 或 SVG 來源檔案
#   output_dir   - 輸出目錄 (預設: .\platform-assets)
#
# 需求:
#   - ImageMagick (magick 命令)
#   - 安裝方式: winget install ImageMagick.ImageMagick
#              或 choco install imagemagick
#
# 範例:
#   .\generate-app-icons.ps1 app-icon.svg .\output
#   .\generate-app-icons.ps1 app-icon-1024.png
# ============================================

param(
    [Parameter(Position=0)]
    [string]$SourceFile,

    [Parameter(Position=1)]
    [string]$OutputDir = ".\platform-assets"
)

# 顏色輸出函數
function Write-Color {
    param([string]$Text, [string]$Color = "White")
    Write-Host $Text -ForegroundColor $Color
}

Write-Color "════════════════════════════════════════════════" "Blue"
Write-Color "   App Icon Generator (iOS & Android)           " "Blue"
Write-Color "   app-uiux-designer skill (Windows)            " "Blue"
Write-Color "════════════════════════════════════════════════" "Blue"
Write-Host ""

# ============================================
# 函數: 顯示使用方式
# ============================================
function Show-Usage {
    Write-Host @"
使用方式:
  .\generate-app-icons.ps1 [source_image] [output_dir]

參數:
  source_image - PNG (1024x1024) 或 SVG 來源檔案
  output_dir   - 輸出目錄 (預設: .\platform-assets)

範例:
  .\generate-app-icons.ps1 app-icon.svg .\output
  .\generate-app-icons.ps1 app-icon-1024.png
"@
}

# ============================================
# 函數: 檢查 ImageMagick
# ============================================
function Test-ImageMagick {
    $magick = Get-Command magick -ErrorAction SilentlyContinue
    if (-not $magick) {
        Write-Color "✗ 錯誤: 找不到 ImageMagick (magick 命令)" "Red"
        Write-Host ""
        Write-Host "請安裝 ImageMagick:"
        Write-Host "  winget install ImageMagick.ImageMagick"
        Write-Host "  或"
        Write-Host "  choco install imagemagick"
        Write-Host ""
        Write-Host "安裝後請重新開啟終端機"
        return $false
    }
    Write-Color "✓ ImageMagick 可用" "Green"
    return $true
}

# ============================================
# 函數: 調整圖片大小
# ============================================
function Resize-Image {
    param(
        [string]$Source,
        [string]$Output,
        [int]$Size
    )

    magick $Source -resize "${Size}x${Size}" -gravity center -extent "${Size}x${Size}" $Output 2>$null
    return $LASTEXITCODE -eq 0
}

# ============================================
# 函數: SVG 轉 PNG
# ============================================
function Convert-SvgToPng {
    param(
        [string]$SvgFile,
        [string]$PngFile,
        [int]$Size = 1024
    )

    magick -background none -density 300 $SvgFile -resize "${Size}x${Size}" $PngFile 2>$null
    return $LASTEXITCODE -eq 0
}

# ============================================
# 函數: 產生 iOS App Icons
# ============================================
function New-iOSIcons {
    param([string]$Source)

    $iosDir = Join-Path $OutputDir "ios\Assets.xcassets\AppIcon.appiconset"

    Write-Color "┌────────────────────────────────────────┐" "Cyan"
    Write-Color "│  iOS App Icons                         │" "Cyan"
    Write-Color "└────────────────────────────────────────┘" "Cyan"

    New-Item -ItemType Directory -Path $iosDir -Force | Out-Null

    # iOS icon sizes: filename => size
    $iOSIcons = @{
        "Icon-20@2x.png" = 40
        "Icon-20@3x.png" = 60
        "Icon-29@2x.png" = 58
        "Icon-29@3x.png" = 87
        "Icon-40@2x.png" = 80
        "Icon-40@3x.png" = 120
        "Icon-60@2x.png" = 120
        "Icon-60@3x.png" = 180
        "Icon-20.png" = 20
        "Icon-20@2x-ipad.png" = 40
        "Icon-29.png" = 29
        "Icon-29@2x-ipad.png" = 58
        "Icon-40.png" = 40
        "Icon-40@2x-ipad.png" = 80
        "Icon-76.png" = 76
        "Icon-76@2x.png" = 152
        "Icon-83.5@2x.png" = 167
        "Icon-1024.png" = 1024
    }

    foreach ($icon in $iOSIcons.GetEnumerator()) {
        $outputPath = Join-Path $iosDir $icon.Key
        if (Resize-Image -Source $Source -Output $outputPath -Size $icon.Value) {
            Write-Host "  " -NoNewline
            Write-Color "✓" "Green" -NoNewline
            Write-Host " $($icon.Key) ($($icon.Value)x$($icon.Value))"
        }
    }

    # 產生 Contents.json
    $contentsJson = @'
{
  "images" : [
    { "filename" : "Icon-20@2x.png", "idiom" : "iphone", "scale" : "2x", "size" : "20x20" },
    { "filename" : "Icon-20@3x.png", "idiom" : "iphone", "scale" : "3x", "size" : "20x20" },
    { "filename" : "Icon-29@2x.png", "idiom" : "iphone", "scale" : "2x", "size" : "29x29" },
    { "filename" : "Icon-29@3x.png", "idiom" : "iphone", "scale" : "3x", "size" : "29x29" },
    { "filename" : "Icon-40@2x.png", "idiom" : "iphone", "scale" : "2x", "size" : "40x40" },
    { "filename" : "Icon-40@3x.png", "idiom" : "iphone", "scale" : "3x", "size" : "40x40" },
    { "filename" : "Icon-60@2x.png", "idiom" : "iphone", "scale" : "2x", "size" : "60x60" },
    { "filename" : "Icon-60@3x.png", "idiom" : "iphone", "scale" : "3x", "size" : "60x60" },
    { "filename" : "Icon-20.png", "idiom" : "ipad", "scale" : "1x", "size" : "20x20" },
    { "filename" : "Icon-20@2x-ipad.png", "idiom" : "ipad", "scale" : "2x", "size" : "20x20" },
    { "filename" : "Icon-29.png", "idiom" : "ipad", "scale" : "1x", "size" : "29x29" },
    { "filename" : "Icon-29@2x-ipad.png", "idiom" : "ipad", "scale" : "2x", "size" : "29x29" },
    { "filename" : "Icon-40.png", "idiom" : "ipad", "scale" : "1x", "size" : "40x40" },
    { "filename" : "Icon-40@2x-ipad.png", "idiom" : "ipad", "scale" : "2x", "size" : "40x40" },
    { "filename" : "Icon-76.png", "idiom" : "ipad", "scale" : "1x", "size" : "76x76" },
    { "filename" : "Icon-76@2x.png", "idiom" : "ipad", "scale" : "2x", "size" : "76x76" },
    { "filename" : "Icon-83.5@2x.png", "idiom" : "ipad", "scale" : "2x", "size" : "83.5x83.5" },
    { "filename" : "Icon-1024.png", "idiom" : "ios-marketing", "scale" : "1x", "size" : "1024x1024" }
  ],
  "info" : { "author" : "app-uiux-designer", "version" : 1 }
}
'@
    $contentsJson | Set-Content (Join-Path $iosDir "Contents.json") -Encoding UTF8

    Write-Color "► iOS icons 完成: $iosDir" "Green"
}

# ============================================
# 函數: 產生 Android App Icons
# ============================================
function New-AndroidIcons {
    param([string]$Source)

    $androidDir = Join-Path $OutputDir "android"

    Write-Color "┌────────────────────────────────────────┐" "Cyan"
    Write-Color "│  Android App Icons (mipmap)            │" "Cyan"
    Write-Color "└────────────────────────────────────────┘" "Cyan"

    # Android mipmap sizes
    $androidMipmaps = @{
        "mipmap-ldpi" = 36
        "mipmap-mdpi" = 48
        "mipmap-hdpi" = 72
        "mipmap-xhdpi" = 96
        "mipmap-xxhdpi" = 144
        "mipmap-xxxhdpi" = 192
    }

    foreach ($mipmap in $androidMipmaps.GetEnumerator()) {
        $mipmapDir = Join-Path $androidDir $mipmap.Key
        New-Item -ItemType Directory -Path $mipmapDir -Force | Out-Null

        # ic_launcher.png
        $launcherPath = Join-Path $mipmapDir "ic_launcher.png"
        Resize-Image -Source $Source -Output $launcherPath -Size $mipmap.Value | Out-Null

        # ic_launcher_round.png
        $roundPath = Join-Path $mipmapDir "ic_launcher_round.png"
        Resize-Image -Source $Source -Output $roundPath -Size $mipmap.Value | Out-Null

        Write-Host "  " -NoNewline
        Write-Color "✓" "Green" -NoNewline
        Write-Host " $($mipmap.Key)/ic_launcher.png ($($mipmap.Value)x$($mipmap.Value))"
    }

    # Adaptive icon foreground
    Write-Color "┌────────────────────────────────────────┐" "Cyan"
    Write-Color "│  Android Adaptive Icon Foreground      │" "Cyan"
    Write-Color "└────────────────────────────────────────┘" "Cyan"

    foreach ($mipmap in $androidMipmaps.GetEnumerator()) {
        $mipmapDir = Join-Path $androidDir $mipmap.Key
        $adaptiveSize = [math]::Floor($mipmap.Value * 108 / 48)
        $foregroundPath = Join-Path $mipmapDir "ic_launcher_foreground.png"
        Resize-Image -Source $Source -Output $foregroundPath -Size $adaptiveSize | Out-Null

        Write-Host "  " -NoNewline
        Write-Color "✓" "Green" -NoNewline
        Write-Host " $($mipmap.Key)/ic_launcher_foreground.png (${adaptiveSize}x${adaptiveSize})"
    }

    # Play Store icon (512x512)
    $playstoreDir = Join-Path $androidDir "playstore"
    New-Item -ItemType Directory -Path $playstoreDir -Force | Out-Null
    $playstorePath = Join-Path $playstoreDir "ic_launcher-playstore.png"
    Resize-Image -Source $Source -Output $playstorePath -Size 512 | Out-Null
    Write-Host "  " -NoNewline
    Write-Color "✓" "Green" -NoNewline
    Write-Host " playstore/ic_launcher-playstore.png (512x512)"

    # Adaptive Icon XML
    $anydpiDir = Join-Path $androidDir "mipmap-anydpi-v26"
    New-Item -ItemType Directory -Path $anydpiDir -Force | Out-Null

    $launcherXml = @'
<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@drawable/ic_launcher_background"/>
    <foreground android:drawable="@mipmap/ic_launcher_foreground"/>
</adaptive-icon>
'@
    $launcherXml | Set-Content (Join-Path $anydpiDir "ic_launcher.xml") -Encoding UTF8
    $launcherXml | Set-Content (Join-Path $anydpiDir "ic_launcher_round.xml") -Encoding UTF8

    Write-Color "► Android icons 完成: $androidDir" "Green"
}

# ============================================
# 主程式
# ============================================

# 尋找預設來源檔案
if (-not $SourceFile) {
    $defaultPaths = @(
        ".\app-icon\app-icon-1024.png",
        ".\app-icon\app-icon-source.svg",
        ".\app-icon.png",
        ".\app-icon.svg"
    )
    foreach ($path in $defaultPaths) {
        if (Test-Path $path) {
            $SourceFile = $path
            break
        }
    }

    if (-not $SourceFile) {
        Write-Color "✗ 錯誤: 請提供來源圖檔" "Red"
        Write-Host ""
        Show-Usage
        exit 1
    }
}

# 檢查檔案存在
if (-not (Test-Path $SourceFile)) {
    Write-Color "✗ 錯誤: 找不到檔案 $SourceFile" "Red"
    exit 1
}

# 檢查 ImageMagick
if (-not (Test-ImageMagick)) {
    exit 1
}
Write-Host ""

# 處理來源檔案
$sourceExt = [System.IO.Path]::GetExtension($SourceFile).ToLower()
$appIconDir = Join-Path $OutputDir "app-icon"
New-Item -ItemType Directory -Path $appIconDir -Force | Out-Null

$sourcePng = Join-Path $appIconDir "app-icon-1024.png"

if ($sourceExt -eq ".svg") {
    Write-Color "► 轉換 SVG 為 PNG..." "Yellow"
    if (Convert-SvgToPng -SvgFile $SourceFile -PngFile $sourcePng -Size 1024) {
        Write-Color "✓ SVG 已轉換" "Green"
        # 複製 SVG 來源
        Copy-Item $SourceFile (Join-Path $appIconDir "app-icon-source.svg") -Force
    } else {
        Write-Color "✗ SVG 轉換失敗" "Red"
        exit 1
    }
} elseif ($sourceExt -eq ".png") {
    Copy-Item $SourceFile $sourcePng -Force
} else {
    Write-Color "✗ 不支援的格式: $sourceExt (僅支援 PNG, SVG)" "Red"
    exit 1
}

Write-Color "► 來源: $SourceFile" "Green"
Write-Color "► 輸出: $OutputDir" "Green"
Write-Host ""

# 產生 icons
New-iOSIcons -Source $sourcePng
Write-Host ""
New-AndroidIcons -Source $sourcePng
Write-Host ""

# 完成摘要
Write-Color "════════════════════════════════════════════════" "Green"
Write-Color "   ✓ App Icons 產生完成!                        " "Green"
Write-Color "════════════════════════════════════════════════" "Green"
Write-Host ""
Write-Host "輸出目錄結構:"
Write-Host ""
Write-Color "$OutputDir/" "Blue"
Write-Host "├── app-icon/"
Write-Host "│   ├── app-icon-1024.png     (來源 PNG)"
Write-Host "│   └── app-icon-source.svg   (來源 SVG)"
Write-Host "├── ios/"
Write-Host "│   └── Assets.xcassets/"
Write-Host "│       └── AppIcon.appiconset/  (18 個 PNG + Contents.json)"
Write-Host "└── android/"
Write-Host "    ├── mipmap-ldpi/    ~ mipmap-xxxhdpi/"
Write-Host "    ├── mipmap-anydpi-v26/  (Adaptive Icon XML)"
Write-Host "    └── playstore/      (512x512)"
Write-Host ""
Write-Color "整合方式:" "Yellow"
Write-Host "  iOS:     將 Assets.xcassets 拖入 Xcode"
Write-Host "  Android: 複製 mipmap-* 到 app/src/main/res/"
Write-Host ""
