#!/bin/bash

# =============================================================================
# convert-to-iphone.sh
# iPad HTML -> iPhone HTML 轉換腳本 (v2.0)
#
# 功能:
#   - 保留模組子目錄結構 (iphone/auth/, iphone/vocab/, etc.)
#   - 支援 CSS 變數替換 (--ipad-width → --iphone-width)
#   - 支援硬編碼像素值替換 (1194px → 393px)
#   - 自動更新導航連結
#
# 使用方式:
#   cd {PROJECT}/04-ui-flow
#   bash ~/.claude/skills/app-uiux-designer.skill/templates/ui-flow/scripts/convert-to-iphone.sh
#
# =============================================================================

set -e

# 顏色輸出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║     iPad → iPhone HTML 轉換工具 v2.0                       ║"
echo "║     保留模組子目錄結構 + CSS 變數支援                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# 確認當前目錄
if [ ! -f "index.html" ]; then
    echo -e "${RED}錯誤：請在 04-ui-flow 目錄下執行此腳本${NC}"
    echo "用法: cd {PROJECT}/04-ui-flow && bash convert-to-iphone.sh"
    exit 1
fi

# 自動偵測模組目錄
echo -e "${CYAN}📁 偵測模組目錄...${NC}"
MODULES=()
for dir in */; do
    dir_name="${dir%/}"
    # 排除特殊目錄
    if [[ "$dir_name" != "iphone" && "$dir_name" != "docs" && "$dir_name" != "shared" && "$dir_name" != "workspace" && "$dir_name" != "screenshots" ]]; then
        # 檢查目錄內是否有 SCR-*.html 檔案
        if ls "$dir_name"/SCR-*.html 1> /dev/null 2>&1; then
            MODULES+=("$dir_name")
            count=$(ls "$dir_name"/SCR-*.html 2>/dev/null | wc -l | tr -d ' ')
            echo "   ✓ $dir_name ($count 個畫面)"
        fi
    fi
done

if [ ${#MODULES[@]} -eq 0 ]; then
    echo -e "${RED}錯誤：未找到任何模組目錄${NC}"
    exit 1
fi

echo ""
echo -e "${CYAN}📱 開始轉換...${NC}"
echo ""

# 計數器
total_converted=0
total_errors=0

# 處理每個模組
for module in "${MODULES[@]}"; do
    # 創建 iPhone 模組目錄
    mkdir -p "iphone/$module"

    module_count=0

    # 處理該模組下的所有 SCR-*.html 檔案
    for ipad_file in "$module"/SCR-*.html; do
        if [ ! -f "$ipad_file" ]; then
            continue
        fi

        filename=$(basename "$ipad_file")
        iphone_file="iphone/$module/$filename"

        # 使用 sed 進行轉換
        # 1. CSS 變數替換 (優先)
        # 2. 硬編碼像素值替換 (備用)
        # 3. 導航連結更新

        if command -v sed &> /dev/null; then
            # 先複製檔案
            cp "$ipad_file" "$iphone_file"

            # 判斷 sed 版本 (macOS vs GNU)
            if sed --version 2>&1 | grep -q GNU; then
                # GNU sed (Linux)
                SED_INPLACE="sed -i"
            else
                # BSD sed (macOS)
                SED_INPLACE="sed -i ''"
            fi

            # 建立臨時檔案進行替換
            temp_file=$(mktemp)

            cat "$ipad_file" | \
                # CSS 變數替換
                sed 's/width: var(--ipad-width);/width: var(--iphone-width);/g' | \
                sed 's/height: var(--ipad-height);/height: var(--iphone-height);/g' | \
                # 硬編碼像素值替換 (body style)
                sed 's/width: 1194px;/width: 393px;/g' | \
                sed 's/height: 834px;/height: 852px;/g' | \
                # viewport meta 替換
                sed 's/width=1194, height=834/width=393, height=852/g' | \
                # CSS :root 變數定義保持不變 (讓 media query 生效)
                # 導航連結: 同模組內的連結 (SCR-XXX.html → 保持相對路徑)
                # 導航連結: 跨模組連結 (../auth/SCR-XXX.html → ../auth/SCR-XXX.html)
                cat > "$temp_file"

            mv "$temp_file" "$iphone_file"

            ((module_count++))
            ((total_converted++))
        else
            echo -e "${RED}  ✗ $filename (sed 不可用)${NC}"
            ((total_errors++))
        fi
    done

    echo -e "   ${GREEN}✓${NC} $module: $module_count 個檔案"
done

echo ""
echo "════════════════════════════════════════════════════════════"
echo -e "${BOLD}📊 轉換結果${NC}"
echo "════════════════════════════════════════════════════════════"

# 統計
ipad_count=$(find . -name "SCR-*.html" -not -path "./iphone/*" -not -path "./docs/*" 2>/dev/null | wc -l | tr -d ' ')
iphone_count=$(find ./iphone -name "SCR-*.html" 2>/dev/null | wc -l | tr -d ' ')

echo "   iPad 畫面:   $ipad_count"
echo "   iPhone 畫面: $iphone_count"
echo "   轉換成功:    $total_converted"
echo "   轉換失敗:    $total_errors"
echo ""

# 驗證
if [ "$iphone_count" -eq "$ipad_count" ]; then
    echo -e "${GREEN}${BOLD}✅ 驗證通過：iPad ($ipad_count) = iPhone ($iphone_count)${NC}"
else
    echo -e "${YELLOW}⚠️  警告：iPad ($ipad_count) != iPhone ($iphone_count)${NC}"
fi

# 抽樣檢查
echo ""
echo -e "${CYAN}🔍 抽樣檢查...${NC}"
sample_file=$(find ./iphone -name "SCR-*.html" 2>/dev/null | head -1)
if [ -n "$sample_file" ]; then
    # 檢查 CSS 變數
    if grep -q "var(--iphone-width)" "$sample_file"; then
        echo -e "   ${GREEN}✓${NC} CSS 變數已正確替換"
    elif grep -q "width: 393px" "$sample_file"; then
        echo -e "   ${GREEN}✓${NC} 硬編碼像素值已正確替換"
    else
        echo -e "   ${YELLOW}⚠${NC} 尺寸替換可能未生效，請手動檢查"
    fi
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo -e "${GREEN}${BOLD}✅ 轉換完成！${NC}"
echo ""
echo "下一步:"
echo "  1. 執行驗證腳本確認導航連結"
echo "  2. 更新 ui-flow-diagram-iphone.html"
echo "  3. 更新 device-preview.html 側邊欄"
echo "════════════════════════════════════════════════════════════"
