#!/bin/bash

# =============================================================================
# convert-to-iphone.sh
# iPad HTML -> iPhone HTML 轉換腳本 (支援響應式佈局)
# =============================================================================

set -e

# 顏色輸出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo "======================================"
echo "  iPad -> iPhone HTML 轉換工具"
echo "  (支援響應式佈局)"
echo "======================================"

# 確認當前目錄
if [ ! -f "index.html" ]; then
    echo -e "${RED}錯誤：請在 04-ui-flow 目錄下執行此腳本${NC}"
    exit 1
fi

# 創建 iphone 目錄（如果不存在）
mkdir -p iphone

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

    # ============================================
    # 1. 更新 viewport meta tag
    # ============================================
    # 格式: width=1194, height=834 -> width=393, height=852
    sed -i '' "s/width=1194, height=834/width=393, height=852/g" "$iphone_file" 2>/dev/null || \
    sed -i "s/width=1194, height=834/width=393, height=852/g" "$iphone_file"

    # 格式: width=1194 -> width=393 (without height)
    sed -i '' "s/width=1194/width=393/g" "$iphone_file" 2>/dev/null || \
    sed -i "s/width=1194/width=393/g" "$iphone_file"

    # ============================================
    # 2. 更新 CSS 尺寸 (傳統模板)
    # ============================================
    # body width/height
    sed -i '' "s/width: 1194px; height: 834px/width: 393px; height: 852px/g" "$iphone_file" 2>/dev/null || \
    sed -i "s/width: 1194px; height: 834px/width: 393px; height: 852px/g" "$iphone_file"

    # 單獨的 width
    sed -i '' "s/width: 1194px/width: 393px/g" "$iphone_file" 2>/dev/null || \
    sed -i "s/width: 1194px/width: 393px/g" "$iphone_file"

    # 單獨的 height (body 高度)
    sed -i '' "s/height: 834px/height: 852px/g" "$iphone_file" 2>/dev/null || \
    sed -i "s/height: 834px/height: 852px/g" "$iphone_file"

    # ============================================
    # 3. 更新 CSS 變數 (響應式模板)
    # ============================================
    # --ipad-width: 1194px -> --iphone-width: 393px
    sed -i '' "s/--ipad-width: 1194px/--iphone-width: 393px/g" "$iphone_file" 2>/dev/null || \
    sed -i "s/--ipad-width: 1194px/--iphone-width: 393px/g" "$iphone_file"

    # --ipad-height: 834px -> --iphone-height: 852px
    sed -i '' "s/--ipad-height: 834px/--iphone-height: 852px/g" "$iphone_file" 2>/dev/null || \
    sed -i "s/--ipad-height: 834px/--iphone-height: 852px/g" "$iphone_file"

    # 更新 body 使用的 CSS 變數
    sed -i '' "s/var(--ipad-width)/var(--iphone-width)/g" "$iphone_file" 2>/dev/null || \
    sed -i "s/var(--ipad-width)/var(--iphone-width)/g" "$iphone_file"

    sed -i '' "s/var(--ipad-height)/var(--iphone-height)/g" "$iphone_file" 2>/dev/null || \
    sed -i "s/var(--ipad-height)/var(--iphone-height)/g" "$iphone_file"

    # ============================================
    # 4. 更新導航連結
    # ============================================
    # 同模組內連結: location.href='SCR- -> location.href='../iphone/SCR-
    sed -i '' "s|location.href='SCR-|location.href='../iphone/SCR-|g" "$iphone_file" 2>/dev/null || \
    sed -i "s|location.href='SCR-|location.href='../iphone/SCR-|g" "$iphone_file"

    # 跨模組連結: location.href='../auth/SCR- -> location.href='../iphone/SCR-
    sed -i '' "s|location.href='\.\./[a-z]*/SCR-|location.href='../iphone/SCR-|g" "$iphone_file" 2>/dev/null || \
    sed -i "s|location.href='\.\./[a-z]*/SCR-|location.href='../iphone/SCR-|g" "$iphone_file"

    # href 屬性連結
    sed -i '' "s|href=\"\.\./[a-z]*/SCR-|href=\"../iphone/SCR-|g" "$iphone_file" 2>/dev/null || \
    sed -i "s|href=\"\.\./[a-z]*/SCR-|href=\"../iphone/SCR-|g" "$iphone_file"

    # ============================================
    # 5. 更新 shared 資源路徑
    # ============================================
    # ../shared/ 保持不變（iphone 目錄在根目錄下）

    echo -e "${GREEN}完成${NC}"
done

echo ""
echo "======================================"
echo -e "${GREEN}轉換完成！${NC}"
echo "已轉換: $(find iphone -name "SCR-*.html" 2>/dev/null | wc -l | tr -d ' ') 個檔案"
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
sample_file=$(find iphone -name "SCR-*.html" 2>/dev/null | head -1)
if [ -n "$sample_file" ]; then
    if grep -q "393" "$sample_file"; then
        echo -e "${GREEN}✅ viewport/尺寸已正確替換為 iPhone 尺寸${NC}"
    else
        echo -e "${RED}❌ 尺寸替換失敗${NC}"
    fi

    # 檢查導航連結
    if grep -q "iphone/SCR-" "$sample_file"; then
        echo -e "${GREEN}✅ 導航連結已更新為 iPhone 路徑${NC}"
    else
        echo -e "${CYAN}ℹ️  此畫面沒有導航連結或使用響應式導航${NC}"
    fi
fi

echo ""
echo "======================================"
echo -e "${GREEN}轉換完成！${NC}"
echo ""
echo "提示："
echo "- 響應式畫面會自動適應 iPhone 尺寸"
echo "- 請在 device-preview.html 中設定 USE_IPHONE_SCREENS = true"
echo "======================================"
