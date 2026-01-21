#!/bin/bash
# ============================================================================
# Exit Validation: 03-generation
# ============================================================================
# Purpose: Validate that 03-generation phase is complete before proceeding
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
echo -e "${BLUE}  Exit Validation: 03-generation${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

ERRORS=0

# Check 1: Screen count
echo -e "${BLUE}[1/6] Screen Count${NC}"
IPAD_COUNT=$(find . -name "SCR-*.html" -not -path "./iphone/*" -not -path "./docs/*" 2>/dev/null | wc -l | tr -d ' ')
IPHONE_COUNT=$(find ./iphone -name "SCR-*.html" 2>/dev/null | wc -l | tr -d ' ')

echo -e "  ${BLUE}📱${NC} iPad screens:  $IPAD_COUNT"
echo -e "  ${BLUE}📱${NC} iPhone screens: $IPHONE_COUNT"

if [ "$IPAD_COUNT" -eq 0 ]; then
    echo -e "  ${RED}❌${NC} No iPad screens generated"
    ERRORS=$((ERRORS+1))
elif [ "$IPAD_COUNT" -ne "$IPHONE_COUNT" ]; then
    echo -e "  ${RED}❌${NC} iPad/iPhone count mismatch ($IPAD_COUNT vs $IPHONE_COUNT)"
    ERRORS=$((ERRORS+1))
else
    echo -e "  ${GREEN}✅${NC} iPad/iPhone counts match"
fi

# Check 2: onclick coverage
echo ""
echo -e "${BLUE}[2/6] onclick Coverage${NC}"
BUTTONS_WITHOUT_ONCLICK=$(find . -name "SCR-*.html" -not -path "./iphone/*" -not -path "./docs/*" -exec grep -l '<button' {} \; 2>/dev/null | xargs grep -h '<button' 2>/dev/null | grep -cv 'onclick=' || echo "0")
if [ "$BUTTONS_WITHOUT_ONCLICK" -eq 0 ]; then
    echo -e "  ${GREEN}✅${NC} All buttons have onclick"
else
    echo -e "  ${RED}❌${NC} $BUTTONS_WITHOUT_ONCLICK buttons without onclick"
    ERRORS=$((ERRORS+1))
fi

# Check 3: No alert placeholders
echo ""
echo -e "${BLUE}[3/6] Alert Placeholders${NC}"
ALERT_COUNT=$(grep -r "onclick=\"alert(" --include="SCR-*.html" . 2>/dev/null | grep -v "./iphone/" | wc -l | tr -d ' ')
if [ "$ALERT_COUNT" -eq 0 ]; then
    echo -e "  ${GREEN}✅${NC} No alert placeholders"
else
    echo -e "  ${RED}❌${NC} Found $ALERT_COUNT alert placeholders"
    ERRORS=$((ERRORS+1))
fi

# Check 4: index.html populated
echo ""
echo -e "${BLUE}[4/6] index.html Content${NC}"
if [ -f "index.html" ]; then
    UNREPLACED=$(grep -c '{{' index.html 2>/dev/null || echo "0")
    if [ "$UNREPLACED" -eq 0 ]; then
        echo -e "  ${GREEN}✅${NC} No unreplaced variables in index.html"
    else
        echo -e "  ${RED}❌${NC} $UNREPLACED unreplaced variables in index.html"
        ERRORS=$((ERRORS+1))
    fi
    
    SCREEN_LINKS=$(grep -c 'openScreen\|screen-link' index.html 2>/dev/null || echo "0")
    echo -e "  ${BLUE}📊${NC} Screen links in index.html: $SCREEN_LINKS"
else
    echo -e "  ${RED}❌${NC} index.html missing"
    ERRORS=$((ERRORS+1))
fi

# Check 5: device-preview.html synchronized
echo ""
echo -e "${BLUE}[5/6] device-preview.html Sidebar${NC}"
if [ -f "device-preview.html" ]; then
    SIDEBAR_COUNT=$(grep -c 'screen-item' device-preview.html 2>/dev/null || echo "0")
    echo -e "  ${BLUE}📊${NC} Sidebar items: $SIDEBAR_COUNT"
    
    if [ "$SIDEBAR_COUNT" -eq "$IPAD_COUNT" ]; then
        echo -e "  ${GREEN}✅${NC} Sidebar synchronized"
    else
        echo -e "  ${RED}❌${NC} Sidebar ($SIDEBAR_COUNT) ≠ screens ($IPAD_COUNT)"
        ERRORS=$((ERRORS+1))
    fi
else
    echo -e "  ${RED}❌${NC} device-preview.html missing"
    ERRORS=$((ERRORS+1))
fi

# Check 6: Diagram files exist
echo ""
echo -e "${BLUE}[6/6] Diagram Files${NC}"
if [ -f "docs/ui-flow-diagram-ipad.html" ]; then
    echo -e "  ${GREEN}✅${NC} ui-flow-diagram-ipad.html exists"
else
    echo -e "  ${YELLOW}⚠️${NC} ui-flow-diagram-ipad.html missing (will be created in 05-diagram)"
fi

if [ -f "docs/ui-flow-diagram-iphone.html" ]; then
    echo -e "  ${GREEN}✅${NC} ui-flow-diagram-iphone.html exists"
else
    echo -e "  ${YELLOW}⚠️${NC} ui-flow-diagram-iphone.html missing (will be created in 05-diagram)"
fi

# Summary
echo ""
echo -e "${BLUE}============================================${NC}"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ 03-generation Exit Validation PASSED${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}❌ 03-generation Exit Validation FAILED${NC}"
    echo -e "   Errors: $ERRORS"
    echo ""
    exit 1
fi
