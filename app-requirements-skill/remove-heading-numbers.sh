#!/bin/bash
# ============================================================================
# remove-heading-numbers.sh
# 移除 Markdown 檔案中標題的手動編號
#
# 用途：確保 MD 檔案不含手動編號，以便 DOCX 轉換時正確自動編號
#
# 使用方式：
#   bash remove-heading-numbers.sh <input.md>
#   bash remove-heading-numbers.sh <input.md> <output.md>
#
# 範例：
#   bash remove-heading-numbers.sh SRS-Project-1.0.md
#   bash remove-heading-numbers.sh SRS-Project-1.0.md SRS-Project-cleaned.md
#
# 處理的編號格式：
#   ## 1. Introduction       -> ## Introduction
#   ### 1.1 Document Purpose -> ### Document Purpose
#   #### 1.1.1 Overview      -> #### Overview
#   ##### 1.1.1.1 Details    -> ##### Details
# ============================================================================

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 檢查參數
if [ $# -lt 1 ]; then
    echo -e "${RED}錯誤：請提供輸入檔案${NC}"
    echo "使用方式: $0 <input.md> [output.md]"
    exit 1
fi

INPUT_FILE="$1"
OUTPUT_FILE="${2:-$INPUT_FILE}"

# 檢查檔案是否存在
if [ ! -f "$INPUT_FILE" ]; then
    echo -e "${RED}錯誤：找不到檔案 '$INPUT_FILE'${NC}"
    exit 1
fi

# 建立備份
BACKUP_FILE="${INPUT_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
cp "$INPUT_FILE" "$BACKUP_FILE"
echo -e "${YELLOW}已建立備份：$BACKUP_FILE${NC}"

# 計算移除前的手動編號數量
BEFORE_COUNT=$(grep -cE '^#{1,6} [0-9]+\.' "$INPUT_FILE" || echo 0)

# 使用 sed 移除手動編號
# 處理格式：## X. / ## X.Y / ## X.Y.Z / ## X.Y.Z.W / ## X.Y.Z.W.V
sed -E '
  s/^(#{1,6}) ([0-9]+\.) /\1 /
  s/^(#{1,6}) ([0-9]+\.[0-9]+) /\1 /
  s/^(#{1,6}) ([0-9]+\.[0-9]+\.[0-9]+) /\1 /
  s/^(#{1,6}) ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+) /\1 /
  s/^(#{1,6}) ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+) /\1 /
' "$BACKUP_FILE" > "$OUTPUT_FILE"

# 計算移除後的手動編號數量
AFTER_COUNT=$(grep -cE '^#{1,6} [0-9]+\.' "$OUTPUT_FILE" || echo 0)
REMOVED_COUNT=$((BEFORE_COUNT - AFTER_COUNT))

# 輸出結果
if [ "$REMOVED_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ 成功移除 $REMOVED_COUNT 個手動編號${NC}"
    echo -e "${GREEN}   輸出檔案：$OUTPUT_FILE${NC}"

    # 顯示一些變更範例
    echo ""
    echo "變更範例："
    diff "$BACKUP_FILE" "$OUTPUT_FILE" | grep -E '^[<>].*^#{1,6}' | head -6 || true
else
    echo -e "${YELLOW}ℹ️  檔案中沒有發現手動編號${NC}"
fi

# 如果輸出檔案與輸入檔案相同，詢問是否刪除備份
if [ "$INPUT_FILE" = "$OUTPUT_FILE" ]; then
    echo ""
    echo -e "${YELLOW}提示：備份檔案保留於 $BACKUP_FILE${NC}"
    echo "如需刪除備份，請執行：rm \"$BACKUP_FILE\""
fi

echo ""
echo "完成！"
