#!/bin/bash

# =============================================================================
# convert-to-iphone.sh
# iPad HTML -> iPhone HTML 轉換腳本
# =============================================================================

set -e

# 顏色輸出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "======================================"
echo "  iPad -> iPhone HTML 轉換工具"
echo "======================================"

# 確認當前目錄
if [ ! -f "index.html" ]; then
    echo -e "${RED}錯誤：請在 04-ui-flow 目錄下執行此腳本${NC}"
    exit 1
fi

# 創建 iphone 目錄（如果不存在）
mkdir -p iphone

# 計數器
converted=0
skipped=0

# iPad 尺寸正則
IPAD_VIEWPORT_PATTERN='width=1194'
IPAD_WIDTH_PATTERN='width: 1194px'
IPAD_HEIGHT_PATTERN='height: 834px'

# iPhone 尺寸
IPHONE_VIEWPORT='width=393'
IPHONE_WIDTH='width: 393px'
IPHONE_HEIGHT='height: 852px'

echo ""
echo "正在搜尋 iPad HTML 檔案..."

# 找到所有 SCR-*.html 檔案（排除 iphone 目錄）
find . -name "SCR-*.html" -not -path "./iphone/*" | while read -r ipad_file; do
    # 取得檔案名稱
    filename=$(basename "$ipad_file")

    # iPhone 輸出路徑
    iphone_file="iphone/$filename"

    echo -n "轉換: $filename ... "

    # 複製檔案
    cp "$ipad_file" "$iphone_file"

    # 替換 viewport
    sed -i '' "s/width=1194, height=834/width=393, height=852/g" "$iphone_file" 2>/dev/null || \
    sed -i "s/width=1194, height=834/width=393, height=852/g" "$iphone_file"

    # 替換 body 尺寸
    sed -i '' "s/width: 1194px; height: 834px/width: 393px; height: 852px/g" "$iphone_file" 2>/dev/null || \
    sed -i "s/width: 1194px; height: 834px/width: 393px; height: 852px/g" "$iphone_file"

    # 替換單獨的 width
    sed -i '' "s/width: 1194px/width: 393px/g" "$iphone_file" 2>/dev/null || \
    sed -i "s/width: 1194px/width: 393px/g" "$iphone_file"

    # 替換單獨的 height (body 高度)
    sed -i '' "s/height: 834px/height: 852px/g" "$iphone_file" 2>/dev/null || \
    sed -i "s/height: 834px/height: 852px/g" "$iphone_file"

    # 更新相對路徑 (../ -> ../)  - 保持不變，因為 iphone 目錄在同一層
    # 但需要更新內部連結指向 iphone 版本
    sed -i '' "s|location.href='SCR-|location.href='../iphone/SCR-|g" "$iphone_file" 2>/dev/null || \
    sed -i "s|location.href='SCR-|location.href='../iphone/SCR-|g" "$iphone_file"

    # 更新跨模組連結 (e.g., ../auth/SCR- -> ../iphone/SCR-)
    sed -i '' "s|location.href='\.\./[^/]*/SCR-|location.href='../iphone/SCR-|g" "$iphone_file" 2>/dev/null || \
    sed -i "s|location.href='\.\./[^/]*/SCR-|location.href='../iphone/SCR-|g" "$iphone_file"

    echo -e "${GREEN}完成${NC}"

    ((converted++)) || true
done

echo ""
echo "======================================"
echo -e "${GREEN}轉換完成！${NC}"
echo "已轉換: $(find iphone -name "SCR-*.html" | wc -l | tr -d ' ') 個檔案"
echo "======================================"

# 驗證
echo ""
echo "驗證轉換結果..."

# 檢查 iPhone 目錄內容
iphone_count=$(find iphone -name "SCR-*.html" 2>/dev/null | wc -l | tr -d ' ')
ipad_count=$(find . -name "SCR-*.html" -not -path "./iphone/*" 2>/dev/null | wc -l | tr -d ' ')

if [ "$iphone_count" -eq "$ipad_count" ]; then
    echo -e "${GREEN}✅ 驗證通過：iPad ($ipad_count) = iPhone ($iphone_count)${NC}"
else
    echo -e "${YELLOW}⚠️  警告：iPad ($ipad_count) != iPhone ($iphone_count)${NC}"
fi

# 抽樣檢查尺寸替換
echo ""
echo "抽樣檢查尺寸..."
sample_file=$(find iphone -name "SCR-*.html" | head -1)
if [ -n "$sample_file" ]; then
    if grep -q "width=393" "$sample_file"; then
        echo -e "${GREEN}✅ viewport 已正確替換為 iPhone 尺寸${NC}"
    else
        echo -e "${RED}❌ viewport 替換失敗${NC}"
    fi
fi

echo ""
echo "轉換完成！請執行驗證腳本確認所有連結正確。"
