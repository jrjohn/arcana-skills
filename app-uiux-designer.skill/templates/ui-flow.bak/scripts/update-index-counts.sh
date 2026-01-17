#!/bin/bash

# =============================================================================
# update-index-counts.sh
# 更新 index.html 中的統計數據
# =============================================================================

set -e

# 顏色輸出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "======================================"
echo "  index.html 統計更新工具"
echo "======================================"

# 確認當前目錄
if [ ! -f "index.html" ]; then
    echo -e "${RED}錯誤：請在 04-ui-flow 目錄下執行此腳本${NC}"
    exit 1
fi

# 計算各模組畫面數量
calculate_module_count() {
    local module_prefix=$1
    find . -name "SCR-${module_prefix}-*.html" -not -path "./iphone/*" 2>/dev/null | wc -l | tr -d ' '
}

# 計算 iPad 和 iPhone 畫面數量
IPAD_SCREENS=$(find . -name "SCR-*.html" -not -path "./iphone/*" 2>/dev/null | wc -l | tr -d ' ')
IPHONE_SCREENS=$(find iphone -name "SCR-*.html" 2>/dev/null | wc -l | tr -d ' ')
TOTAL_SCREENS=$IPAD_SCREENS

# 計算各模組數量
AUTH_COUNT=$(calculate_module_count "AUTH")
ONBOARD_COUNT=$(calculate_module_count "ONBOARD")
DASH_COUNT=$(calculate_module_count "DASH")
VOCAB_COUNT=$(calculate_module_count "VOCAB")
TRAIN_COUNT=$(calculate_module_count "TRAIN")
PROGRESS_COUNT=$(calculate_module_count "PROG")
REPORT_COUNT=$(calculate_module_count "REPORT")
SETTING_COUNT=$(calculate_module_count "SETTING")
FEATURE_COUNT=$(calculate_module_count "FEATURE")
PARENT_COUNT=$(calculate_module_count "PARENT")
HOME_COUNT=$(calculate_module_count "HOME")

# 計算覆蓋率 (如果 iPad 和 iPhone 都有就是 100%)
if [ "$IPHONE_SCREENS" -eq "$IPAD_SCREENS" ] && [ "$IPAD_SCREENS" -gt 0 ]; then
    COVERAGE=100
else
    if [ "$IPAD_SCREENS" -gt 0 ]; then
        COVERAGE=$((IPHONE_SCREENS * 100 / IPAD_SCREENS))
    else
        COVERAGE=0
    fi
fi

echo ""
echo "統計結果："
echo "  iPad 畫面數：$IPAD_SCREENS"
echo "  iPhone 畫面數：$IPHONE_SCREENS"
echo "  覆蓋率：$COVERAGE%"
echo ""
echo "模組統計："
echo "  AUTH: $AUTH_COUNT"
echo "  ONBOARD: $ONBOARD_COUNT"
echo "  DASH: $DASH_COUNT"
echo "  VOCAB: $VOCAB_COUNT"
echo "  TRAIN: $TRAIN_COUNT"
echo "  PROGRESS: $PROGRESS_COUNT"
echo "  REPORT: $REPORT_COUNT"
echo "  SETTING: $SETTING_COUNT"
echo "  PARENT: $PARENT_COUNT"
echo "  HOME: $HOME_COUNT"

# 備份 index.html
cp index.html index.html.bak

echo ""
echo "正在更新 index.html..."

# 替換變數
sed -i '' "s/{{TOTAL_SCREENS}}/$TOTAL_SCREENS/g" index.html 2>/dev/null || \
sed -i "s/{{TOTAL_SCREENS}}/$TOTAL_SCREENS/g" index.html

sed -i '' "s/{{IPAD_SCREENS}}/$IPAD_SCREENS/g" index.html 2>/dev/null || \
sed -i "s/{{IPAD_SCREENS}}/$IPAD_SCREENS/g" index.html

sed -i '' "s/{{IPHONE_SCREENS}}/$IPHONE_SCREENS/g" index.html 2>/dev/null || \
sed -i "s/{{IPHONE_SCREENS}}/$IPHONE_SCREENS/g" index.html

sed -i '' "s/{{COVERAGE}}/$COVERAGE/g" index.html 2>/dev/null || \
sed -i "s/{{COVERAGE}}/$COVERAGE/g" index.html

# 替換各模組數量
sed -i '' "s/{{AUTH_COUNT}}/$AUTH_COUNT/g" index.html 2>/dev/null || \
sed -i "s/{{AUTH_COUNT}}/$AUTH_COUNT/g" index.html

sed -i '' "s/{{ONBOARD_COUNT}}/$ONBOARD_COUNT/g" index.html 2>/dev/null || \
sed -i "s/{{ONBOARD_COUNT}}/$ONBOARD_COUNT/g" index.html

sed -i '' "s/{{DASH_COUNT}}/$DASH_COUNT/g" index.html 2>/dev/null || \
sed -i "s/{{DASH_COUNT}}/$DASH_COUNT/g" index.html

sed -i '' "s/{{VOCAB_COUNT}}/$VOCAB_COUNT/g" index.html 2>/dev/null || \
sed -i "s/{{VOCAB_COUNT}}/$VOCAB_COUNT/g" index.html

sed -i '' "s/{{TRAIN_COUNT}}/$TRAIN_COUNT/g" index.html 2>/dev/null || \
sed -i "s/{{TRAIN_COUNT}}/$TRAIN_COUNT/g" index.html

sed -i '' "s/{{PROGRESS_COUNT}}/$PROGRESS_COUNT/g" index.html 2>/dev/null || \
sed -i "s/{{PROGRESS_COUNT}}/$PROGRESS_COUNT/g" index.html

sed -i '' "s/{{REPORT_COUNT}}/$REPORT_COUNT/g" index.html 2>/dev/null || \
sed -i "s/{{REPORT_COUNT}}/$REPORT_COUNT/g" index.html

sed -i '' "s/{{SETTING_COUNT}}/$SETTING_COUNT/g" index.html 2>/dev/null || \
sed -i "s/{{SETTING_COUNT}}/$SETTING_COUNT/g" index.html

sed -i '' "s/{{FEATURE_COUNT}}/$FEATURE_COUNT/g" index.html 2>/dev/null || \
sed -i "s/{{FEATURE_COUNT}}/$FEATURE_COUNT/g" index.html

sed -i '' "s/{{PARENT_COUNT}}/$PARENT_COUNT/g" index.html 2>/dev/null || \
sed -i "s/{{PARENT_COUNT}}/$PARENT_COUNT/g" index.html

sed -i '' "s/{{HOME_COUNT}}/$HOME_COUNT/g" index.html 2>/dev/null || \
sed -i "s/{{HOME_COUNT}}/$HOME_COUNT/g" index.html

# 檢查是否還有未替換的變數
remaining=$(grep -o '{{[^}]*}}' index.html 2>/dev/null | wc -l | tr -d ' ')

echo ""
if [ "$remaining" -eq 0 ]; then
    echo -e "${GREEN}✅ 所有變數已替換完成${NC}"
    rm -f index.html.bak
else
    echo -e "${YELLOW}⚠️  警告：還有 $remaining 個未替換的變數${NC}"
    grep -o '{{[^}]*}}' index.html | sort | uniq
fi

echo ""
echo "更新完成！"
