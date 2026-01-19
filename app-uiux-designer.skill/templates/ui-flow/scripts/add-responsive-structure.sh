#!/bin/bash

# =============================================================================
# add-responsive-structure.sh
# 為現有 iPad HTML 添加響應式結構
# =============================================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "======================================"
echo "  添加響應式結構到所有畫面"
echo "======================================"

# 確認當前目錄
if [ ! -f "index.html" ]; then
    echo -e "${YELLOW}請在 04-ui-flow 目錄下執行此腳本${NC}"
    exit 1
fi

# 新的 head 結構
RESPONSIVE_HEAD='<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PLACEHOLDER_TITLE</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    screens: {
                        '\''phone'\'': {'\''max'\'': '\''500px'\''},
                        '\''tablet'\'': {'\''min'\'': '\''501px'\''},
                    }
                }
            }
        }
    </script>
    <style>
        :root {
            --ipad-width: 1194px;
            --ipad-height: 834px;
            --iphone-width: 393px;
            --iphone-height: 852px;
        }
        body {
            width: var(--ipad-width);
            height: var(--ipad-height);
            overflow: hidden;
            margin: 0;
            padding: 0;
        }
        @media (max-width: 500px) {
            body {
                width: var(--iphone-width);
                height: var(--iphone-height);
            }
        }
    </style>
</head>'

count=0
find . -name "SCR-*.html" -not -path "./iphone/*" | while read -r file; do
    filename=$(basename "$file")

    # 跳過已經有響應式結構的檔案
    if grep -q "tailwind.config" "$file"; then
        echo -e "${GREEN}跳過 (已有響應式): $filename${NC}"
        continue
    fi

    # 提取現有 title
    title=$(grep -o '<title>[^<]*</title>' "$file" | sed 's/<[^>]*>//g')

    echo "處理: $filename"

    # 1. 更新 viewport
    sed -i '' 's/width=1194, height=834/width=device-width/g' "$file" 2>/dev/null || \
    sed -i 's/width=1194, height=834/width=device-width/g' "$file"

    # 2. 添加 tailwind.config (在 </script> 後的第一個 <style> 前)
    # 先檢查是否已有 tailwind.config
    if ! grep -q "tailwind.config" "$file"; then
        # 在 </head> 前添加 tailwind config
        sed -i '' 's|<script src="https://cdn.tailwindcss.com"></script>|<script src="https://cdn.tailwindcss.com"></script>\
    <script>\
        tailwind.config = {\
            theme: {\
                extend: {\
                    screens: {\
                        '\''phone'\'': {'\''max'\'': '\''500px'\''},\
                        '\''tablet'\'': {'\''min'\'': '\''501px'\''},\
                    }\
                }\
            }\
        }\
    </script>|' "$file" 2>/dev/null || true
    fi

    # 3. 更新 body 尺寸為 CSS 變數
    sed -i '' 's/width: 1194px;/width: var(--ipad-width);/g' "$file" 2>/dev/null || \
    sed -i 's/width: 1194px;/width: var(--ipad-width);/g' "$file"

    sed -i '' 's/height: 834px;/height: var(--ipad-height);/g' "$file" 2>/dev/null || \
    sed -i 's/height: 834px;/height: var(--ipad-height);/g' "$file"

    # 4. 添加 CSS 變數和媒體查詢 (如果沒有)
    if ! grep -q "\-\-ipad-width" "$file"; then
        sed -i '' 's|<style>|<style>\
        :root {\
            --ipad-width: 1194px;\
            --ipad-height: 834px;\
            --iphone-width: 393px;\
            --iphone-height: 852px;\
        }|' "$file" 2>/dev/null || true
    fi

    if ! grep -q "@media (max-width: 500px)" "$file"; then
        sed -i '' 's|overflow: hidden;|overflow: hidden;\
        }\
        @media (max-width: 500px) {\
            body {\
                width: var(--iphone-width);\
                height: var(--iphone-height);\
            }|' "$file" 2>/dev/null || true
    fi

    count=$((count + 1))
done

echo ""
echo "======================================"
echo -e "${GREEN}完成！${NC}"
echo "已處理畫面數量"
echo ""
echo "下一步：手動為每個畫面添加 tablet: 響應式類別"
echo "======================================"
