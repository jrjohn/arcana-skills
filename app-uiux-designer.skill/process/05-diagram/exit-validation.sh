#!/bin/bash
# ============================================================================
# Exit Validation: 05-diagram
# ============================================================================
# Purpose: Validate that 05-diagram phase is complete before proceeding
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
echo -e "${BLUE}  Exit Validation: 05-diagram${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

ERRORS=0
IPAD_COUNT=$(find . -name "SCR-*.html" -not -path "./iphone/*" -not -path "./docs/*" 2>/dev/null | wc -l | tr -d ' ')

# Check 1: Diagram files exist
echo -e "${BLUE}[1/5] Diagram Files${NC}"
if [ -f "docs/ui-flow-diagram.html" ]; then
    echo -e "  ${GREEN}✅${NC} docs/ui-flow-diagram.html (device selector)"
else
    echo -e "  ${RED}❌${NC} docs/ui-flow-diagram.html missing"
    ERRORS=$((ERRORS+1))
fi

if [ -f "docs/ui-flow-diagram-ipad.html" ]; then
    echo -e "  ${GREEN}✅${NC} docs/ui-flow-diagram-ipad.html"
else
    echo -e "  ${RED}❌${NC} docs/ui-flow-diagram-ipad.html missing"
    ERRORS=$((ERRORS+1))
fi

if [ -f "docs/ui-flow-diagram-iphone.html" ]; then
    echo -e "  ${GREEN}✅${NC} docs/ui-flow-diagram-iphone.html"
else
    echo -e "  ${RED}❌${NC} docs/ui-flow-diagram-iphone.html missing"
    ERRORS=$((ERRORS+1))
fi

# Check 2: Screen card count
echo ""
echo -e "${BLUE}[2/5] Screen Card Count${NC}"
if [ -f "docs/ui-flow-diagram-ipad.html" ]; then
    IPAD_CARDS=$(grep -c 'screen-card' docs/ui-flow-diagram-ipad.html 2>/dev/null || echo "0")
    echo -e "  ${BLUE}📊${NC} iPad diagram cards: $IPAD_CARDS / Expected: $IPAD_COUNT"
    if [ "$IPAD_CARDS" -eq "$IPAD_COUNT" ]; then
        echo -e "  ${GREEN}✅${NC} iPad card count matches"
    else
        echo -e "  ${RED}❌${NC} iPad card count mismatch"
        ERRORS=$((ERRORS+1))
    fi
fi

if [ -f "docs/ui-flow-diagram-iphone.html" ]; then
    IPHONE_CARDS=$(grep -c 'screen-card' docs/ui-flow-diagram-iphone.html 2>/dev/null || echo "0")
    echo -e "  ${BLUE}📊${NC} iPhone diagram cards: $IPHONE_CARDS / Expected: $IPAD_COUNT"
    if [ "$IPHONE_CARDS" -eq "$IPAD_COUNT" ]; then
        echo -e "  ${GREEN}✅${NC} iPhone card count matches"
    else
        echo -e "  ${RED}❌${NC} iPhone card count mismatch"
        ERRORS=$((ERRORS+1))
    fi
fi

# Check 3: Arrow count (minimum 10)
echo ""
echo -e "${BLUE}[3/5] Navigation Arrows${NC}"
if [ -f "docs/ui-flow-diagram-ipad.html" ]; then
    IPAD_ARROWS=$(grep -c 'marker-end' docs/ui-flow-diagram-ipad.html 2>/dev/null || echo "0")
    echo -e "  ${BLUE}➡️${NC} iPad arrows: $IPAD_ARROWS"
    if [ "$IPAD_ARROWS" -ge 10 ]; then
        echo -e "  ${GREEN}✅${NC} iPad arrows >= 10"
    else
        echo -e "  ${RED}❌${NC} iPad arrows < 10 (need at least 10)"
        ERRORS=$((ERRORS+1))
    fi
fi

if [ -f "docs/ui-flow-diagram-iphone.html" ]; then
    IPHONE_ARROWS=$(grep -c 'marker-end' docs/ui-flow-diagram-iphone.html 2>/dev/null || echo "0")
    echo -e "  ${BLUE}➡️${NC} iPhone arrows: $IPHONE_ARROWS"
    if [ "$IPHONE_ARROWS" -ge 10 ]; then
        echo -e "  ${GREEN}✅${NC} iPhone arrows >= 10"
    else
        echo -e "  ${RED}❌${NC} iPhone arrows < 10 (need at least 10)"
        ERRORS=$((ERRORS+1))
    fi
fi

# Check 4: No negative X coordinates in arrows
echo ""
echo -e "${BLUE}[4/5] Arrow Boundary Check${NC}"
IPAD_NEG_X=$(grep -E 'Q -[0-9]+|L -[0-9]+|M -[0-9]+' docs/ui-flow-diagram-ipad.html 2>/dev/null | wc -l | tr -d ' ')
IPHONE_NEG_X=$(grep -E 'Q -[0-9]+|L -[0-9]+|M -[0-9]+' docs/ui-flow-diagram-iphone.html 2>/dev/null | wc -l | tr -d ' ')

if [ "$IPAD_NEG_X" -eq 0 ]; then
    echo -e "  ${GREEN}✅${NC} iPad: No negative X coordinates"
else
    echo -e "  ${RED}❌${NC} iPad: $IPAD_NEG_X arrows with negative X"
    ERRORS=$((ERRORS+1))
fi

if [ "$IPHONE_NEG_X" -eq 0 ]; then
    echo -e "  ${GREEN}✅${NC} iPhone: No negative X coordinates"
else
    echo -e "  ${RED}❌${NC} iPhone: $IPHONE_NEG_X arrows with negative X"
    ERRORS=$((ERRORS+1))
fi

# Check 5: No placeholders
echo ""
echo -e "${BLUE}[5/5] Placeholder Check${NC}"
IPAD_PLACEHOLDERS=$(grep -c 'PLACEHOLDER\|{{' docs/ui-flow-diagram-ipad.html 2>/dev/null || echo "0")
IPHONE_PLACEHOLDERS=$(grep -c 'PLACEHOLDER\|{{' docs/ui-flow-diagram-iphone.html 2>/dev/null || echo "0")

if [ "$IPAD_PLACEHOLDERS" -eq 0 ]; then
    echo -e "  ${GREEN}✅${NC} iPad: No placeholders"
else
    echo -e "  ${RED}❌${NC} iPad: $IPAD_PLACEHOLDERS placeholders found"
    ERRORS=$((ERRORS+1))
fi

if [ "$IPHONE_PLACEHOLDERS" -eq 0 ]; then
    echo -e "  ${GREEN}✅${NC} iPhone: No placeholders"
else
    echo -e "  ${RED}❌${NC} iPhone: $IPHONE_PLACEHOLDERS placeholders found"
    ERRORS=$((ERRORS+1))
fi

# Summary
echo ""
echo -e "${BLUE}============================================${NC}"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ 05-diagram Exit Validation PASSED${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}❌ 05-diagram Exit Validation FAILED${NC}"
    echo -e "   Errors: $ERRORS"
    echo ""
    exit 1
fi
