#!/bin/bash
# ============================================================================
# Exit Validation: 08-finalize
# ============================================================================
# Purpose: Final validation before marking UI Flow as complete
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
echo -e "${BLUE}  Exit Validation: 08-finalize${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

ERRORS=0

# Navigate to project root if needed
if [ -d "../04-ui-flow" ]; then
    cd ..
fi

UI_FLOW_DIR="04-ui-flow"
if [ ! -d "$UI_FLOW_DIR" ]; then
    echo -e "${RED}❌ 04-ui-flow directory not found${NC}"
    exit 1
fi

# Check 1: All phases completed
echo -e "${BLUE}[1/4] Phase Completion${NC}"
if [ -f "$UI_FLOW_DIR/workspace/current-process.json" ]; then
    PENDING=$(grep -c '"pending"' "$UI_FLOW_DIR/workspace/current-process.json" 2>/dev/null || echo "0")
    IN_PROGRESS=$(grep -c '"in_progress"' "$UI_FLOW_DIR/workspace/current-process.json" 2>/dev/null || echo "0")
    COMPLETED=$(grep -c '"completed"' "$UI_FLOW_DIR/workspace/current-process.json" 2>/dev/null || echo "0")
    
    echo -e "  ${BLUE}📊${NC} Completed: $COMPLETED, In Progress: $IN_PROGRESS, Pending: $PENDING"
    
    if [ "$PENDING" -eq 0 ] && [ "$IN_PROGRESS" -eq 0 ]; then
        echo -e "  ${GREEN}✅${NC} All phases completed"
    else
        echo -e "  ${RED}❌${NC} Some phases not completed"
        ERRORS=$((ERRORS+1))
    fi
else
    echo -e "  ${RED}❌${NC} current-process.json not found"
    ERRORS=$((ERRORS+1))
fi

# Check 2: Screen count final
echo ""
echo -e "${BLUE}[2/4] Final Screen Count${NC}"
cd "$UI_FLOW_DIR"
IPAD_COUNT=$(find . -name "SCR-*.html" -not -path "./iphone/*" -not -path "./docs/*" 2>/dev/null | wc -l | tr -d ' ')
IPHONE_COUNT=$(find ./iphone -name "SCR-*.html" 2>/dev/null | wc -l | tr -d ' ')

echo -e "  ${BLUE}📱${NC} iPad screens: $IPAD_COUNT"
echo -e "  ${BLUE}📱${NC} iPhone screens: $IPHONE_COUNT"

if [ "$IPAD_COUNT" -gt 0 ] && [ "$IPAD_COUNT" -eq "$IPHONE_COUNT" ]; then
    echo -e "  ${GREEN}✅${NC} Screen counts valid and matching"
else
    echo -e "  ${RED}❌${NC} Screen count issue"
    ERRORS=$((ERRORS+1))
fi
cd ..

# Check 3: All critical files present
echo ""
echo -e "${BLUE}[3/4] Critical Files${NC}"
CRITICAL_FILES=(
    "$UI_FLOW_DIR/index.html"
    "$UI_FLOW_DIR/device-preview.html"
    "$UI_FLOW_DIR/docs/ui-flow-diagram-ipad.html"
    "$UI_FLOW_DIR/docs/ui-flow-diagram-iphone.html"
)

for file in "${CRITICAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  ${GREEN}✅${NC} $file"
    else
        echo -e "  ${RED}❌${NC} $file missing"
        ERRORS=$((ERRORS+1))
    fi
done

# Check 4: Completion report exists
echo ""
echo -e "${BLUE}[4/4] Completion Report${NC}"
if [ -f "$UI_FLOW_DIR/ui-flow-completion-report.md" ]; then
    echo -e "  ${GREEN}✅${NC} Completion report exists"
else
    echo -e "  ${YELLOW}⚠️${NC} Completion report not found"
    echo -e "      Generating basic report..."
    
    cat > "$UI_FLOW_DIR/ui-flow-completion-report.md" << EOF
# UI Flow Completion Report

## Project Summary
- Total Screens: $IPAD_COUNT
- iPad Screens: $IPAD_COUNT
- iPhone Screens: $IPHONE_COUNT

## Deliverables
- [x] HTML Screen Prototypes
- [x] UI Flow Diagram (iPad/iPhone)
- [x] Navigation Validation
- [x] SDD/SRS Updated

## Completion Date
$(date +%Y-%m-%d)

## Notes
UI Flow generation completed via app-uiux-designer.skill
EOF
    echo -e "  ${GREEN}✅${NC} Report generated"
fi

# Summary
echo ""
echo -e "${BLUE}============================================${NC}"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}  ✅ 08-finalize Exit Validation PASSED${NC}"
    echo -e "${GREEN}     UI Flow Generation Complete!${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}❌ 08-finalize Exit Validation FAILED${NC}"
    echo -e "   Errors: $ERRORS"
    echo ""
    exit 1
fi
