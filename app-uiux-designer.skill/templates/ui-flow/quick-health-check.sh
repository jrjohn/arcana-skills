#!/bin/bash
# ============================================================================
# Quick Health Check - Compaction Recovery Protocol
# ============================================================================
# Purpose: Rapidly assess project state after Claude compaction
# Usage: bash quick-health-check.sh [project-04-ui-flow-path]
# ============================================================================

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_PATH="${1:-.}"
cd "$PROJECT_PATH"

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}       Quick Health Check${NC}"
echo -e "${BLUE}       Compaction Recovery Protocol${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

ERRORS=0
WARNINGS=0

# ============================================================================
# 1. Workspace Check
# ============================================================================
echo -e "${BLUE}[1/6] Workspace Check${NC}"
if [ -d "workspace" ]; then
  echo -e "  ${GREEN}✅${NC} workspace/ exists"
else
  echo -e "  ${RED}❌${NC} workspace/ missing - creating..."
  mkdir -p workspace/{context,state}
  WARNINGS=$((WARNINGS+1))
fi

# ============================================================================
# 2. Current Process State
# ============================================================================
echo ""
echo -e "${BLUE}[2/6] Current Process State${NC}"
if [ -f "workspace/current-process.json" ]; then
  CURRENT_PROCESS=$(cat workspace/current-process.json 2>/dev/null | grep -o '"current_process": "[^"]*"' | cut -d'"' -f4 || echo "unknown")
  LAST_UPDATED=$(cat workspace/current-process.json 2>/dev/null | grep -o '"last_updated": "[^"]*"' | cut -d'"' -f4 || echo "unknown")
  echo -e "  ${GREEN}✅${NC} current-process.json exists"
  echo -e "  ${BLUE}📍${NC} Current Node: ${YELLOW}$CURRENT_PROCESS${NC}"
  echo -e "  ${BLUE}🕐${NC} Last Updated: $LAST_UPDATED"

  # Extract progress
  echo -e "  ${BLUE}📊${NC} Progress:"
  grep -oE '"[0-9]+-[^"]+": "[^"]+"' workspace/current-process.json | while read -r line; do
    node=$(echo "$line" | cut -d'"' -f2)
    status=$(echo "$line" | cut -d'"' -f4)
    case $status in
      completed) echo -e "    ${GREEN}✅${NC} $node" ;;
      in_progress) echo -e "    ${YELLOW}🔄${NC} $node" ;;
      pending) echo -e "    ⬜ $node" ;;
    esac
  done
else
  echo -e "  ${RED}❌${NC} current-process.json missing"
  CURRENT_PROCESS="00-init"
  ERRORS=$((ERRORS+1))
fi

# ============================================================================
# 3. Screen Count
# ============================================================================
echo ""
echo -e "${BLUE}[3/6] Screen Count${NC}"

# iPad screens (not in iphone/ or docs/)
IPAD_COUNT=$(find . -name "SCR-*.html" -not -path "./iphone/*" -not -path "./docs/*" 2>/dev/null | wc -l | tr -d ' ')
# iPhone screens
IPHONE_COUNT=$(find ./iphone -name "SCR-*.html" 2>/dev/null | wc -l | tr -d ' ')

echo -e "  ${BLUE}📱${NC} iPad screens:  ${YELLOW}$IPAD_COUNT${NC}"
echo -e "  ${BLUE}📱${NC} iPhone screens: ${YELLOW}$IPHONE_COUNT${NC}"

if [ "$IPAD_COUNT" -eq 0 ]; then
  echo -e "  ${RED}❌${NC} No iPad screens found!"
  ERRORS=$((ERRORS+1))
elif [ "$IPAD_COUNT" -ne "$IPHONE_COUNT" ]; then
  echo -e "  ${YELLOW}⚠️${NC} iPad/iPhone count mismatch"
  WARNINGS=$((WARNINGS+1))
else
  echo -e "  ${GREEN}✅${NC} iPad/iPhone counts match"
fi

# ============================================================================
# 4. Critical Files Check
# ============================================================================
echo ""
echo -e "${BLUE}[4/6] Critical Files${NC}"

CRITICAL_FILES=(
  "index.html"
  "device-preview.html"
  "docs/ui-flow-diagram-ipad.html"
  "docs/ui-flow-diagram-iphone.html"
)

for file in "${CRITICAL_FILES[@]}"; do
  if [ -f "$file" ]; then
    echo -e "  ${GREEN}✅${NC} $file"
  else
    echo -e "  ${RED}❌${NC} $file"
    ERRORS=$((ERRORS+1))
  fi
done

# ============================================================================
# 5. Validation Chain
# ============================================================================
echo ""
echo -e "${BLUE}[5/6] Validation Chain${NC}"
if [ -f "workspace/validation-chain.json" ]; then
  echo -e "  ${GREEN}✅${NC} validation-chain.json exists"
  echo -e "  ${BLUE}📋${NC} Completed validations:"

  # Parse JSON and show completed nodes
  grep -oE '"node": "[^"]*"' workspace/validation-chain.json | cut -d'"' -f4 | while read -r node; do
    result=$(grep -A1 "\"node\": \"$node\"" workspace/validation-chain.json | grep -o '"result": "[^"]*"' | cut -d'"' -f4 || echo "unknown")
    if [ "$result" = "PASSED" ]; then
      echo -e "    ${GREEN}✅${NC} $node - PASSED"
    else
      echo -e "    ${RED}❌${NC} $node - $result"
    fi
  done

  LAST_CHECKPOINT=$(grep -o '"last_valid_checkpoint": "[^"]*"' workspace/validation-chain.json | cut -d'"' -f4 || echo "none")
  echo -e "  ${BLUE}🎯${NC} Last valid checkpoint: ${YELLOW}$LAST_CHECKPOINT${NC}"
else
  echo -e "  ${YELLOW}⚠️${NC} validation-chain.json missing"
  echo -e "      Need to run validations from scratch"
  WARNINGS=$((WARNINGS+1))
fi

# ============================================================================
# 6. index.html Content Check
# ============================================================================
echo ""
echo -e "${BLUE}[6/6] index.html Content Check${NC}"
if [ -f "index.html" ]; then
  # Check for placeholder text
  if grep -q "尚未產生畫面" index.html; then
    echo -e "  ${RED}❌${NC} index.html contains placeholder text '尚未產生畫面'"
    ERRORS=$((ERRORS+1))
  else
    echo -e "  ${GREEN}✅${NC} No placeholder text found"
  fi

  # Check coverage display
  COVERAGE=$(grep -oE 'id="coverage-rate">[^<]+' index.html | sed 's/.*>//' || echo "0%")
  echo -e "  ${BLUE}📊${NC} Displayed coverage: ${YELLOW}$COVERAGE${NC}"

  # Check screen count display
  DISPLAYED_IPAD=$(grep -oE 'id="ipad-count">[^<]+' index.html | sed 's/.*>//' || echo "0")
  echo -e "  ${BLUE}📱${NC} Displayed iPad count: ${YELLOW}$DISPLAYED_IPAD${NC}"

  if [ "$DISPLAYED_IPAD" != "$IPAD_COUNT" ] && [ "$IPAD_COUNT" -gt 0 ]; then
    echo -e "  ${YELLOW}⚠️${NC} Displayed count ($DISPLAYED_IPAD) != actual count ($IPAD_COUNT)"
    WARNINGS=$((WARNINGS+1))
  fi
fi

# ============================================================================
# Summary
# ============================================================================
echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}       Health Check Summary${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo -e "  ${BLUE}📍${NC} Current Node: ${YELLOW}$CURRENT_PROCESS${NC}"
echo -e "  ${BLUE}📊${NC} Screen Count: ${YELLOW}$IPAD_COUNT${NC} (iPad) / ${YELLOW}$IPHONE_COUNT${NC} (iPhone)"
echo -e "  ${RED}❌${NC} Errors: ${YELLOW}$ERRORS${NC}"
echo -e "  ${YELLOW}⚠️${NC}  Warnings: ${YELLOW}$WARNINGS${NC}"
echo ""

if [ $ERRORS -gt 0 ]; then
  echo -e "${RED}🚨 Critical issues found!${NC}"
  echo -e "   Run: node recover-state.js to attempt recovery"
  exit 1
elif [ $WARNINGS -gt 0 ]; then
  echo -e "${YELLOW}⚠️ Some warnings found${NC}"
  echo -e "   Review above and fix if necessary"
  echo -e "   Continue from node: ${YELLOW}$CURRENT_PROCESS${NC}"
  exit 0
else
  echo -e "${GREEN}✅ All checks passed!${NC}"
  echo -e "   Continue from node: ${YELLOW}$CURRENT_PROCESS${NC}"
  exit 0
fi
