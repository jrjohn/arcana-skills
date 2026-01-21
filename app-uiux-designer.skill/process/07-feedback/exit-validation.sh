#!/bin/bash
# ============================================================================
# Exit Validation: 07-feedback
# ============================================================================
# Purpose: Validate that 07-feedback phase is complete before proceeding
# Usage: bash exit-validation.sh [project-path] (parent of 04-ui-flow)
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
echo -e "${BLUE}  Exit Validation: 07-feedback${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

ERRORS=0

# Navigate to project root if we're in 04-ui-flow
if [ -d "../02-design" ]; then
    cd ..
elif [ ! -d "02-design" ]; then
    echo -e "${RED}❌ Cannot find project structure${NC}"
    exit 1
fi

# Check 1: SDD has UI prototype references
echo -e "${BLUE}[1/4] SDD UI Prototype References${NC}"
SDD_FILE=$(ls 02-design/SDD-*.md 2>/dev/null | head -1)
if [ -n "$SDD_FILE" ]; then
    SCREEN_COUNT=$(grep -c "^#### SCR-" "$SDD_FILE" 2>/dev/null || echo "0")
    IPAD_REFS=$(grep -c "images/ipad/SCR-.*\.png" "$SDD_FILE" 2>/dev/null || echo "0")
    IPHONE_REFS=$(grep -c "images/iphone/SCR-.*\.png" "$SDD_FILE" 2>/dev/null || echo "0")
    
    echo -e "  ${BLUE}📊${NC} SDD screens: $SCREEN_COUNT"
    echo -e "  ${BLUE}📸${NC} iPad refs: $IPAD_REFS"
    echo -e "  ${BLUE}📸${NC} iPhone refs: $IPHONE_REFS"
    
    if [ "$IPAD_REFS" -eq "$SCREEN_COUNT" ] && [ "$IPAD_REFS" -gt 0 ]; then
        echo -e "  ${GREEN}✅${NC} All screens have iPad references"
    else
        echo -e "  ${RED}❌${NC} Missing iPad references ($IPAD_REFS / $SCREEN_COUNT)"
        ERRORS=$((ERRORS+1))
    fi
    
    if [ "$IPHONE_REFS" -eq "$SCREEN_COUNT" ] && [ "$IPHONE_REFS" -gt 0 ]; then
        echo -e "  ${GREEN}✅${NC} All screens have iPhone references"
    else
        echo -e "  ${YELLOW}⚠️${NC} Missing iPhone references ($IPHONE_REFS / $SCREEN_COUNT)"
    fi
else
    echo -e "  ${RED}❌${NC} SDD file not found"
    ERRORS=$((ERRORS+1))
fi

# Check 2: SRS has Screen References section
echo ""
echo -e "${BLUE}[2/4] SRS Screen References${NC}"
SRS_FILE=$(ls 01-requirements/SRS-*.md 2>/dev/null | head -1)
if [ -n "$SRS_FILE" ]; then
    if grep -q "Screen References\|SCR 對照\|畫面參考" "$SRS_FILE" 2>/dev/null; then
        echo -e "  ${GREEN}✅${NC} Screen References section exists"
    else
        echo -e "  ${RED}❌${NC} Screen References section missing"
        ERRORS=$((ERRORS+1))
    fi
    
    # Check for SDD traceability
    if grep -q "SDD 追蹤\|SDD Traceability\|SCR-" "$SRS_FILE" 2>/dev/null; then
        echo -e "  ${GREEN}✅${NC} SDD traceability present"
    else
        echo -e "  ${YELLOW}⚠️${NC} SDD traceability may be incomplete"
    fi
else
    echo -e "  ${RED}❌${NC} SRS file not found"
    ERRORS=$((ERRORS+1))
fi

# Check 3: Images exist
echo ""
echo -e "${BLUE}[3/4] Image Files${NC}"
if [ -d "02-design/images/ipad" ]; then
    IPAD_IMAGES=$(find 02-design/images/ipad -name "*.png" 2>/dev/null | wc -l | tr -d ' ')
    echo -e "  ${BLUE}📸${NC} iPad images: $IPAD_IMAGES"
    if [ "$IPAD_IMAGES" -gt 0 ]; then
        echo -e "  ${GREEN}✅${NC} iPad images present"
    else
        echo -e "  ${YELLOW}⚠️${NC} No iPad images found"
    fi
else
    echo -e "  ${YELLOW}⚠️${NC} 02-design/images/ipad/ not found"
fi

if [ -d "02-design/images/iphone" ]; then
    IPHONE_IMAGES=$(find 02-design/images/iphone -name "*.png" 2>/dev/null | wc -l | tr -d ' ')
    echo -e "  ${BLUE}📸${NC} iPhone images: $IPHONE_IMAGES"
    if [ "$IPHONE_IMAGES" -gt 0 ]; then
        echo -e "  ${GREEN}✅${NC} iPhone images present"
    else
        echo -e "  ${YELLOW}⚠️${NC} No iPhone images found"
    fi
else
    echo -e "  ${YELLOW}⚠️${NC} 02-design/images/iphone/ not found"
fi

# Check 4: DOCX files updated
echo ""
echo -e "${BLUE}[4/4] DOCX Files${NC}"
SDD_DOCX=$(ls 02-design/SDD-*.docx 2>/dev/null | head -1)
SRS_DOCX=$(ls 01-requirements/SRS-*.docx 2>/dev/null | head -1)

if [ -n "$SDD_DOCX" ]; then
    DOCX_DATE=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M" "$SDD_DOCX" 2>/dev/null || stat -c "%y" "$SDD_DOCX" 2>/dev/null | cut -d' ' -f1-2 || echo "unknown")
    echo -e "  ${GREEN}✅${NC} SDD.docx exists (modified: $DOCX_DATE)"
else
    echo -e "  ${YELLOW}⚠️${NC} SDD.docx not found"
fi

if [ -n "$SRS_DOCX" ]; then
    DOCX_DATE=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M" "$SRS_DOCX" 2>/dev/null || stat -c "%y" "$SRS_DOCX" 2>/dev/null | cut -d' ' -f1-2 || echo "unknown")
    echo -e "  ${GREEN}✅${NC} SRS.docx exists (modified: $DOCX_DATE)"
else
    echo -e "  ${YELLOW}⚠️${NC} SRS.docx not found"
fi

# Summary
echo ""
echo -e "${BLUE}============================================${NC}"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ 07-feedback Exit Validation PASSED${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}❌ 07-feedback Exit Validation FAILED${NC}"
    echo -e "   Errors: $ERRORS"
    echo ""
    exit 1
fi
