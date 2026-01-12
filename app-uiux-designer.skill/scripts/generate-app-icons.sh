#!/bin/bash

# ============================================
# App Icon Generator for iOS & Android
# ============================================
# 從 1024x1024 PNG/SVG 來源產生所有平台 app icon 尺寸
#
# 使用方式:
#   ./generate-app-icons.sh [source_image] [output_dir]
#
# 參數:
#   source_image - PNG (1024x1024) 或 SVG 來源檔案
#   output_dir   - 輸出目錄 (預設: ./platform-assets)
#
# 支援平台:
#   - macOS (使用 sips 或 ImageMagick)
#   - Linux (使用 ImageMagick)
#   - WSL   (使用 ImageMagick)
#
# 需求 (任一):
#   - sips (macOS 內建)
#   - ImageMagick: brew install imagemagick (macOS)
#                  sudo apt install imagemagick (Linux)
#
# 範例:
#   ./generate-app-icons.sh app-icon.svg ./output
#   ./generate-app-icons.sh app-icon-1024.png
# ============================================

set -e

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 預設參數
SOURCE_FILE="${1:-}"
OUTPUT_DIR="${2:-./platform-assets}"

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   App Icon Generator (iOS & Android)           ║${NC}"
echo -e "${BLUE}║   app-uiux-designer skill                      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo ""

# ============================================
# 函數: 顯示使用方式
# ============================================
show_usage() {
    echo "使用方式:"
    echo "  $0 [source_image] [output_dir]"
    echo ""
    echo "參數:"
    echo "  source_image - PNG (1024x1024) 或 SVG 來源檔案"
    echo "  output_dir   - 輸出目錄 (預設: ./platform-assets)"
    echo ""
    echo "範例:"
    echo "  $0 app-icon.svg ./output"
    echo "  $0 app-icon-1024.png"
    echo ""
}

# ============================================
# 函數: 檢查工具
# ============================================
check_tools() {
    # 檢查圖片處理工具 (優先 sips，備選 ImageMagick)
    RESIZE_TOOL=""

    if command -v sips &> /dev/null; then
        RESIZE_TOOL="sips"
        echo -e "${GREEN}✓${NC} sips 可用 (macOS 原生)"
    elif command -v magick &> /dev/null; then
        RESIZE_TOOL="magick"
        echo -e "${GREEN}✓${NC} ImageMagick (magick) 可用"
    elif command -v convert &> /dev/null; then
        RESIZE_TOOL="convert"
        echo -e "${GREEN}✓${NC} ImageMagick (convert) 可用"
    else
        echo -e "${RED}✗ 錯誤: 找不到圖片處理工具${NC}"
        echo -e "  請安裝以下任一工具:"
        echo -e "    macOS:  sips (內建) 或 brew install imagemagick"
        echo -e "    Linux:  sudo apt install imagemagick"
        echo -e "    所有平台: https://imagemagick.org/script/download.php"
        exit 1
    fi

    # 檢查 SVG 轉換工具
    if command -v rsvg-convert &> /dev/null; then
        SVG_TOOL="rsvg-convert"
        echo -e "${GREEN}✓${NC} rsvg-convert 可用 (SVG 轉換)"
    elif [ "$RESIZE_TOOL" = "magick" ] || [ "$RESIZE_TOOL" = "convert" ]; then
        SVG_TOOL="$RESIZE_TOOL"
        echo -e "${GREEN}✓${NC} ImageMagick 可用 (SVG 轉換)"
    else
        SVG_TOOL=""
        echo -e "${YELLOW}!${NC} 無 SVG 轉換工具 (僅支援 PNG 輸入)"
    fi
}

# ============================================
# 函數: 調整圖片大小 (跨平台)
# ============================================
resize_image() {
    local source="$1"
    local output="$2"
    local size="$3"

    case "$RESIZE_TOOL" in
        sips)
            sips -z "$size" "$size" "$source" --out "$output" > /dev/null 2>&1
            ;;
        magick)
            magick "$source" -resize "${size}x${size}" -gravity center -extent "${size}x${size}" "$output" 2>/dev/null
            ;;
        convert)
            convert "$source" -resize "${size}x${size}" -gravity center -extent "${size}x${size}" "$output" 2>/dev/null
            ;;
    esac
}

# ============================================
# 函數: 轉換 SVG 到 PNG
# ============================================
convert_svg_to_png() {
    local svg_file="$1"
    local png_file="$2"
    local size="${3:-1024}"

    if [ "$SVG_TOOL" = "rsvg-convert" ]; then
        rsvg-convert -w "$size" -h "$size" "$svg_file" -o "$png_file"
    elif [ "$SVG_TOOL" = "convert" ]; then
        convert -background none -density 300 -resize "${size}x${size}" "$svg_file" "$png_file"
    else
        echo -e "${RED}✗ 無法轉換 SVG，請安裝 librsvg 或 ImageMagick${NC}"
        exit 1
    fi
}

# ============================================
# 函數: 產生 iOS App Icons
# ============================================
generate_ios_icons() {
    local source="$1"
    local ios_dir="$OUTPUT_DIR/ios/Assets.xcassets/AppIcon.appiconset"

    echo -e "${CYAN}┌────────────────────────────────────────┐${NC}"
    echo -e "${CYAN}│  iOS App Icons                         │${NC}"
    echo -e "${CYAN}└────────────────────────────────────────┘${NC}"

    mkdir -p "$ios_dir"

    # iOS icon sizes: (filename, size)
    declare -a IOS_ICONS=(
        "Icon-20@2x.png:40"
        "Icon-20@3x.png:60"
        "Icon-29@2x.png:58"
        "Icon-29@3x.png:87"
        "Icon-40@2x.png:80"
        "Icon-40@3x.png:120"
        "Icon-60@2x.png:120"
        "Icon-60@3x.png:180"
        "Icon-20.png:20"
        "Icon-20@2x-ipad.png:40"
        "Icon-29.png:29"
        "Icon-29@2x-ipad.png:58"
        "Icon-40.png:40"
        "Icon-40@2x-ipad.png:80"
        "Icon-76.png:76"
        "Icon-76@2x.png:152"
        "Icon-83.5@2x.png:167"
        "Icon-1024.png:1024"
    )

    for icon_spec in "${IOS_ICONS[@]}"; do
        IFS=':' read -r filename size <<< "$icon_spec"
        output_path="$ios_dir/$filename"
        resize_image "$source" "$output_path" "$size"
        echo -e "  ${GREEN}✓${NC} $filename (${size}x${size})"
    done

    # 產生 Contents.json
    cat > "$ios_dir/Contents.json" << 'EOF'
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
EOF

    echo -e "${GREEN}► iOS icons 完成: $ios_dir${NC}"
}

# ============================================
# 函數: 產生 Android App Icons
# ============================================
generate_android_icons() {
    local source="$1"
    local android_dir="$OUTPUT_DIR/android"

    echo -e "${CYAN}┌────────────────────────────────────────┐${NC}"
    echo -e "${CYAN}│  Android App Icons (mipmap)            │${NC}"
    echo -e "${CYAN}└────────────────────────────────────────┘${NC}"

    # Android mipmap sizes
    declare -a ANDROID_MIPMAPS=(
        "mipmap-ldpi:36"
        "mipmap-mdpi:48"
        "mipmap-hdpi:72"
        "mipmap-xhdpi:96"
        "mipmap-xxhdpi:144"
        "mipmap-xxxhdpi:192"
    )

    for mipmap_spec in "${ANDROID_MIPMAPS[@]}"; do
        IFS=':' read -r folder size <<< "$mipmap_spec"
        output_dir="$android_dir/$folder"
        mkdir -p "$output_dir"

        # ic_launcher.png
        resize_image "$source" "$output_dir/ic_launcher.png" "$size"
        # ic_launcher_round.png
        resize_image "$source" "$output_dir/ic_launcher_round.png" "$size"

        echo -e "  ${GREEN}✓${NC} $folder/ic_launcher.png (${size}x${size})"
    done

    # Adaptive icon foreground (108dp safe zone)
    echo -e "${CYAN}┌────────────────────────────────────────┐${NC}"
    echo -e "${CYAN}│  Android Adaptive Icon Foreground      │${NC}"
    echo -e "${CYAN}└────────────────────────────────────────┘${NC}"

    for mipmap_spec in "${ANDROID_MIPMAPS[@]}"; do
        IFS=':' read -r folder base_size <<< "$mipmap_spec"
        output_dir="$android_dir/$folder"
        adaptive_size=$(echo "$base_size * 108 / 48" | bc)
        resize_image "$source" "$output_dir/ic_launcher_foreground.png" "$adaptive_size"
        echo -e "  ${GREEN}✓${NC} $folder/ic_launcher_foreground.png (${adaptive_size}x${adaptive_size})"
    done

    # Play Store icon (512x512)
    mkdir -p "$android_dir/playstore"
    resize_image "$source" "$android_dir/playstore/ic_launcher-playstore.png" 512
    echo -e "  ${GREEN}✓${NC} playstore/ic_launcher-playstore.png (512x512)"

    # Adaptive Icon XML
    mkdir -p "$android_dir/mipmap-anydpi-v26"
    cat > "$android_dir/mipmap-anydpi-v26/ic_launcher.xml" << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@drawable/ic_launcher_background"/>
    <foreground android:drawable="@mipmap/ic_launcher_foreground"/>
</adaptive-icon>
EOF

    cat > "$android_dir/mipmap-anydpi-v26/ic_launcher_round.xml" << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@drawable/ic_launcher_background"/>
    <foreground android:drawable="@mipmap/ic_launcher_foreground"/>
</adaptive-icon>
EOF

    echo -e "${GREEN}► Android icons 完成: $android_dir${NC}"
}

# ============================================
# 主程式
# ============================================

# 檢查參數
if [ -z "$SOURCE_FILE" ]; then
    # 嘗試尋找預設來源
    if [ -f "./app-icon/app-icon-1024.png" ]; then
        SOURCE_FILE="./app-icon/app-icon-1024.png"
    elif [ -f "./app-icon/app-icon-source.svg" ]; then
        SOURCE_FILE="./app-icon/app-icon-source.svg"
    elif [ -f "./app-icon.png" ]; then
        SOURCE_FILE="./app-icon.png"
    elif [ -f "./app-icon.svg" ]; then
        SOURCE_FILE="./app-icon.svg"
    else
        echo -e "${RED}✗ 錯誤: 請提供來源圖檔${NC}"
        echo ""
        show_usage
        exit 1
    fi
fi

# 檢查檔案存在
if [ ! -f "$SOURCE_FILE" ]; then
    echo -e "${RED}✗ 錯誤: 找不到檔案 $SOURCE_FILE${NC}"
    exit 1
fi

# 檢查工具
check_tools
echo ""

# 處理來源檔案
SOURCE_EXT="${SOURCE_FILE##*.}"
SOURCE_PNG="$OUTPUT_DIR/app-icon/app-icon-1024.png"

mkdir -p "$OUTPUT_DIR/app-icon"

if [ "${SOURCE_EXT,,}" = "svg" ]; then
    echo -e "${YELLOW}► 轉換 SVG 為 PNG...${NC}"
    convert_svg_to_png "$SOURCE_FILE" "$SOURCE_PNG" 1024
    echo -e "${GREEN}✓ SVG 已轉換${NC}"
    # 複製 SVG 來源
    cp "$SOURCE_FILE" "$OUTPUT_DIR/app-icon/app-icon-source.svg"
elif [ "${SOURCE_EXT,,}" = "png" ]; then
    cp "$SOURCE_FILE" "$SOURCE_PNG"
else
    echo -e "${RED}✗ 不支援的格式: $SOURCE_EXT (僅支援 PNG, SVG)${NC}"
    exit 1
fi

echo -e "${GREEN}► 來源: $SOURCE_FILE${NC}"
echo -e "${GREEN}► 輸出: $OUTPUT_DIR${NC}"
echo ""

# 產生 icons
generate_ios_icons "$SOURCE_PNG"
echo ""
generate_android_icons "$SOURCE_PNG"
echo ""

# 完成摘要
echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   ✓ App Icons 產生完成!                        ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════╝${NC}"
echo ""
echo "輸出目錄結構:"
echo ""
echo -e "${BLUE}$OUTPUT_DIR/${NC}"
echo "├── app-icon/"
echo "│   ├── app-icon-1024.png     (來源 PNG)"
echo "│   └── app-icon-source.svg   (來源 SVG)"
echo "├── ios/"
echo "│   └── Assets.xcassets/"
echo "│       └── AppIcon.appiconset/  (18 個 PNG + Contents.json)"
echo "└── android/"
echo "    ├── mipmap-ldpi/    ~ mipmap-xxxhdpi/"
echo "    ├── mipmap-anydpi-v26/  (Adaptive Icon XML)"
echo "    └── playstore/      (512x512)"
echo ""
echo -e "${YELLOW}整合方式:${NC}"
echo "  iOS:     將 Assets.xcassets 拖入 Xcode"
echo "  Android: 複製 mipmap-* 到 app/src/main/res/"
echo ""
