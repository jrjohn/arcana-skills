#!/bin/bash
# ============================================================================
# Exit Validation: 04-validation
# ============================================================================
# Purpose: Validate that 04-validation phase is complete before proceeding
# Usage: bash exit-validation.sh [project-04-ui-flow-path]
# ============================================================================

set -e
PROJECT_PATH="${1:-.}"
cd "$PROJECT_PATH" 2>/dev/null || { echo "Error: Cannot access $PROJECT_PATH"; exit 1; }

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Exit Validation: 04-validation${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

ERRORS=0

# Check 1: Navigation coverage (100%)
echo -e "${BLUE}[1/4] Navigation Coverage${NC}"

# Count buttons/clickable elements without onclick
EMPTY_ONCLICK=$(grep -r 'onclick=""' --include="SCR-*.html" . 2>/dev/null | grep -v "./iphone/" | wc -l | tr -d ' ')
ALERT_ONCLICK=$(grep -r 'onclick="alert' --include="SCR-*.html" . 2>/dev/null | grep -v "./iphone/" | wc -l | tr -d ' ')

if [ "$EMPTY_ONCLICK" -eq 0 ]; then
    echo -e "  ${GREEN}✅${NC} No empty onclick handlers"
else
    echo -e "  ${RED}❌${NC} $EMPTY_ONCLICK empty onclick handlers found"
    ERRORS=$((ERRORS+1))
fi

if [ "$ALERT_ONCLICK" -eq 0 ]; then
    echo -e "  ${GREEN}✅${NC} No alert placeholders"
else
    echo -e "  ${RED}❌${NC} $ALERT_ONCLICK alert placeholders found"
    ERRORS=$((ERRORS+1))
fi

# Check 2: All navigation targets exist
echo ""
echo -e "${BLUE}[2/4] Navigation Target Validation${NC}"
MISSING_TARGETS=0
for file in $(find . -name "SCR-*.html" -not -path "./iphone/*" -not -path "./docs/*" 2>/dev/null); do
    # Extract onclick targets
    targets=$(grep -oE "location\.href='[^']+'" "$file" 2>/dev/null | sed "s/location.href='//g" | sed "s/'//g" || true)
    for target in $targets; do
        # Handle relative paths
        dir=$(dirname "$file")
        target_path="$dir/$target"
        if [ ! -f "$target_path" ] && [ "$target" != "history.back()" ]; then
            # Try from root
            if [ ! -f "$target" ]; then
                MISSING_TARGETS=$((MISSING_TARGETS+1))
            fi
        fi
    done
done

if [ "$MISSING_TARGETS" -eq 0 ]; then
    echo -e "  ${GREEN}✅${NC} All navigation targets exist"
else
    echo -e "  ${YELLOW}⚠️${NC} $MISSING_TARGETS targets may be missing (check paths)"
fi

# Check 3: Consistency validation
echo ""
echo -e "${BLUE}[3/4] Consistency Check${NC}"
IPAD_COUNT=$(find . -name "SCR-*.html" -not -path "./iphone/*" -not -path "./docs/*" 2>/dev/null | wc -l | tr -d ' ')
IPHONE_COUNT=$(find ./iphone -name "SCR-*.html" 2>/dev/null | wc -l | tr -d ' ')

if [ "$IPAD_COUNT" -eq "$IPHONE_COUNT" ]; then
    echo -e "  ${GREEN}✅${NC} iPad/iPhone counts match: $IPAD_COUNT"
else
    echo -e "  ${RED}❌${NC} iPad ($IPAD_COUNT) ≠ iPhone ($IPHONE_COUNT)"
    ERRORS=$((ERRORS+1))
fi

# Check device-preview sidebar
SIDEBAR_COUNT=$(grep -c 'screen-item' device-preview.html 2>/dev/null || echo "0")
if [ "$SIDEBAR_COUNT" -eq "$IPAD_COUNT" ]; then
    echo -e "  ${GREEN}✅${NC} device-preview sidebar synchronized"
else
    echo -e "  ${RED}❌${NC} Sidebar ($SIDEBAR_COUNT) ≠ Screens ($IPAD_COUNT)"
    ERRORS=$((ERRORS+1))
fi

# Check 4: Validation report exists (optional)
echo ""
echo -e "${BLUE}[4/4] Validation Report${NC}"
if [ -f "workspace/validation-report.json" ]; then
    echo -e "  ${GREEN}✅${NC} workspace/validation-report.json exists"
else
    echo -e "  ${YELLOW}⚠️${NC} validation-report.json not found"
fi

# Summary
echo ""
echo -e "${BLUE}============================================${NC}"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ 04-validation Exit Validation PASSED${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}❌ 04-validation Exit Validation FAILED${NC}"
    echo -e "   Errors: $ERRORS"
    echo ""
    exit 1
fi
