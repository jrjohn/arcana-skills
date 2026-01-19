#!/bin/bash
# ============================================================================
# Keyword Trigger Prediction Check
# ============================================================================
# 檢查 SRS/用戶需求中的關鍵字並預測缺失模組
# Usage: bash keyword-prediction-check.sh <project-dir>
# ============================================================================

set -e

PROJECT_DIR="${1:-.}"
SRS_FILE=$(ls "$PROJECT_DIR/01-requirements/SRS-"*.md 2>/dev/null | head -1)
SDD_FILE=$(ls "$PROJECT_DIR/02-design/SDD-"*.md 2>/dev/null | head -1)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  關鍵字觸發預測檢查${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

if [ ! -f "$SRS_FILE" ]; then
  echo -e "${RED}❌ SRS 檔案不存在${NC}"
  exit 1
fi

if [ ! -f "$SDD_FILE" ]; then
  echo -e "${RED}❌ SDD 檔案不存在${NC}"
  exit 1
fi

echo -e "${BLUE}📄 SRS: ${NC}$SRS_FILE"
echo -e "${BLUE}📄 SDD: ${NC}$SDD_FILE"
echo ""

MISSING_MODULES=0
RECOMMENDATIONS=""

# ============================================================================
# ENGAGE 模組檢測
# ============================================================================
echo -e "${BLUE}[1/6] 檢測 ENGAGE 模組關鍵字...${NC}"
ENGAGE_KEYWORDS="黏著度|留存|活躍|遊戲化|gamification|徽章|badge|獎勵|reward|寵物|pet|商店|shop|排行榜|leaderboard|連續|streak|簽到"

if grep -qiE "$ENGAGE_KEYWORDS" "$SRS_FILE"; then
  MATCHED=$(grep -oiE "$ENGAGE_KEYWORDS" "$SRS_FILE" | head -3 | tr '\n' ', ')
  echo -e "  ${YELLOW}⚠️ 檢測到關鍵字: ${NC}$MATCHED"

  if grep -q "SCR-ENGAGE" "$SDD_FILE"; then
    ENGAGE_COUNT=$(grep -c "SCR-ENGAGE" "$SDD_FILE" 2>/dev/null || echo "0")
    echo -e "  ${GREEN}✅ SDD 已有 ENGAGE 模組 ($ENGAGE_COUNT 個畫面)${NC}"
  else
    echo -e "  ${RED}❌ SDD 缺少 ENGAGE 模組！${NC}"
    echo -e "  ${YELLOW}   建議新增: pet, accessories, shop, badges, leaderboard, daily-reward (6 畫面)${NC}"
    MISSING_MODULES=$((MISSING_MODULES+1))
    RECOMMENDATIONS="$RECOMMENDATIONS\n- 新增 ENGAGE 模組 (6 畫面)"
  fi
else
  echo -e "  ${GREEN}✓ 未檢測到 ENGAGE 關鍵字${NC}"
fi

# ============================================================================
# SOCIAL 模組檢測
# ============================================================================
echo ""
echo -e "${BLUE}[2/6] 檢測 SOCIAL 模組關鍵字...${NC}"
SOCIAL_KEYWORDS="公開|public|分享|share|社群|community|邀請|invite|好友|friend|回饋|feedback"

if grep -qiE "$SOCIAL_KEYWORDS" "$SRS_FILE"; then
  MATCHED=$(grep -oiE "$SOCIAL_KEYWORDS" "$SRS_FILE" | head -3 | tr '\n' ', ')
  echo -e "  ${YELLOW}⚠️ 檢測到關鍵字: ${NC}$MATCHED"

  if grep -q "SCR-SOCIAL" "$SDD_FILE"; then
    SOCIAL_COUNT=$(grep -c "SCR-SOCIAL" "$SDD_FILE" 2>/dev/null || echo "0")
    echo -e "  ${GREEN}✅ SDD 已有 SOCIAL 模組 ($SOCIAL_COUNT 個畫面)${NC}"
  else
    echo -e "  ${RED}❌ SDD 缺少 SOCIAL 模組！${NC}"
    echo -e "  ${YELLOW}   建議新增: share, public-list, invite, feedback (4 畫面)${NC}"
    MISSING_MODULES=$((MISSING_MODULES+1))
    RECOMMENDATIONS="$RECOMMENDATIONS\n- 新增 SOCIAL 模組 (4 畫面)"
  fi
else
  echo -e "  ${GREEN}✓ 未檢測到 SOCIAL 關鍵字${NC}"
fi

# ============================================================================
# VOCAB 擴充檢測
# ============================================================================
echo ""
echo -e "${BLUE}[3/6] 檢測 VOCAB 擴充關鍵字...${NC}"
VOCAB_EXT_KEYWORDS="合併|merge|分群|group|分類|category|匯出|export|導出|批次|batch|發布|publish"

if grep -qiE "$VOCAB_EXT_KEYWORDS" "$SRS_FILE"; then
  MATCHED=$(grep -oiE "$VOCAB_EXT_KEYWORDS" "$SRS_FILE" | head -3 | tr '\n' ', ')
  echo -e "  ${YELLOW}⚠️ 檢測到關鍵字: ${NC}$MATCHED"

  VOCAB_COUNT=$(grep -c "SCR-VOCAB" "$SDD_FILE" 2>/dev/null || echo "0")
  if [ "$VOCAB_COUNT" -lt 12 ]; then
    echo -e "  ${YELLOW}⚠️ VOCAB 模組可能不完整 (現有 $VOCAB_COUNT，建議 12+)${NC}"
    echo -e "  ${YELLOW}   建議補充: edit-word, export, merge, group, filter, batch, publish, ocr-result${NC}"
    MISSING_MODULES=$((MISSING_MODULES+1))
    RECOMMENDATIONS="$RECOMMENDATIONS\n- 擴充 VOCAB 模組 (+$((12-VOCAB_COUNT)) 畫面)"
  else
    echo -e "  ${GREEN}✅ VOCAB 模組完整 ($VOCAB_COUNT 個畫面)${NC}"
  fi
else
  echo -e "  ${GREEN}✓ 未檢測到 VOCAB 擴充關鍵字${NC}"
fi

# ============================================================================
# PROGRESS 擴充檢測
# ============================================================================
echo ""
echo -e "${BLUE}[4/6] 檢測 PROGRESS 擴充關鍵字...${NC}"
PROGRESS_EXT_KEYWORDS="報表|report|統計|statistics|週報|weekly|日曆|calendar|趨勢|trend|排名|ranking"

if grep -qiE "$PROGRESS_EXT_KEYWORDS" "$SRS_FILE"; then
  MATCHED=$(grep -oiE "$PROGRESS_EXT_KEYWORDS" "$SRS_FILE" | head -3 | tr '\n' ', ')
  echo -e "  ${YELLOW}⚠️ 檢測到關鍵字: ${NC}$MATCHED"

  PROGRESS_COUNT=$(grep -c "SCR-PROGRESS" "$SDD_FILE" 2>/dev/null || echo "0")
  if [ "$PROGRESS_COUNT" -lt 6 ]; then
    echo -e "  ${YELLOW}⚠️ PROGRESS 模組可能不完整 (現有 $PROGRESS_COUNT，建議 6+)${NC}"
    echo -e "  ${YELLOW}   建議補充: weekly, calendar, skills, trend, ranking, daily${NC}"
    MISSING_MODULES=$((MISSING_MODULES+1))
    RECOMMENDATIONS="$RECOMMENDATIONS\n- 擴充 PROGRESS 模組 (+$((6-PROGRESS_COUNT)) 畫面)"
  else
    echo -e "  ${GREEN}✅ PROGRESS 模組完整 ($PROGRESS_COUNT 個畫面)${NC}"
  fi
else
  echo -e "  ${GREEN}✓ 未檢測到 PROGRESS 擴充關鍵字${NC}"
fi

# ============================================================================
# TRAIN 擴充檢測
# ============================================================================
echo ""
echo -e "${BLUE}[5/6] 檢測 TRAIN 擴充關鍵字...${NC}"
TRAIN_EXT_KEYWORDS="冒險|adventure|關卡|level|stage|混合|mixed|綜合|闘關|挑戰|challenge"

if grep -qiE "$TRAIN_EXT_KEYWORDS" "$SRS_FILE"; then
  MATCHED=$(grep -oiE "$TRAIN_EXT_KEYWORDS" "$SRS_FILE" | head -3 | tr '\n' ', ')
  echo -e "  ${YELLOW}⚠️ 檢測到關鍵字: ${NC}$MATCHED"

  TRAIN_COUNT=$(grep -c "SCR-TRAIN" "$SDD_FILE" 2>/dev/null || echo "0")
  if [ "$TRAIN_COUNT" -lt 12 ]; then
    echo -e "  ${YELLOW}⚠️ TRAIN 模組可能不完整 (現有 $TRAIN_COUNT，建議 12+)${NC}"
    echo -e "  ${YELLOW}   建議補充: mixed, adventure-map, level-start, challenge${NC}"
    MISSING_MODULES=$((MISSING_MODULES+1))
    RECOMMENDATIONS="$RECOMMENDATIONS\n- 擴充 TRAIN 模組 (+$((12-TRAIN_COUNT)) 畫面)"
  else
    echo -e "  ${GREEN}✅ TRAIN 模組完整 ($TRAIN_COUNT 個畫面)${NC}"
  fi
else
  echo -e "  ${GREEN}✓ 未檢測到 TRAIN 擴充關鍵字${NC}"
fi

# ============================================================================
# SETTING 擴充檢測
# ============================================================================
echo ""
echo -e "${BLUE}[6/6] 檢測 SETTING 擴充關鍵字...${NC}"
SETTING_EXT_KEYWORDS="條款|terms|隱私政策|privacy.policy|授權|license|更新日誌|changelog|幫助|help|FAQ"

SETTING_COUNT=$(grep -c "SCR-SETTING" "$SDD_FILE" 2>/dev/null || echo "0")
if [ "$SETTING_COUNT" -lt 15 ]; then
  echo -e "  ${YELLOW}⚠️ SETTING 模組可能不完整 (現有 $SETTING_COUNT，建議 15+)${NC}"
  echo -e "  ${YELLOW}   建議補充: terms, privacy-policy, licenses, changelog, help, learning, reminder, sync, theme${NC}"
  MISSING_MODULES=$((MISSING_MODULES+1))
  RECOMMENDATIONS="$RECOMMENDATIONS\n- 擴充 SETTING 模組 (+$((15-SETTING_COUNT)) 畫面)"
else
  echo -e "  ${GREEN}✅ SETTING 模組完整 ($SETTING_COUNT 個畫面)${NC}"
fi

# ============================================================================
# 總結
# ============================================================================
echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  檢查結果${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# 計算現有畫面數
TOTAL_SCREENS=$(grep -c "^#### SCR-" "$SDD_FILE" 2>/dev/null || echo "0")
echo -e "${BLUE}📊 SDD 現有畫面數: ${NC}$TOTAL_SCREENS"

if [ "$MISSING_MODULES" -eq 0 ]; then
  echo ""
  echo -e "${GREEN}✅ 所有關鍵字觸發預測檢查通過${NC}"
  echo -e "${GREEN}   模組設計完整，符合用戶需求${NC}"
  exit 0
else
  echo ""
  echo -e "${RED}❌ 發現 $MISSING_MODULES 個模組需要補充${NC}"
  echo ""
  echo -e "${YELLOW}建議行動:${NC}"
  echo -e "$RECOMMENDATIONS"
  echo ""
  echo -e "${YELLOW}⚠️ 請在 Step 5 補充上述預測畫面後再進入 Phase 3${NC}"
  exit 1
fi
