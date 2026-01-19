#!/bin/bash
# ============================================================================
# Exit Validation - 05-diagram
# ============================================================================
# Must pass before marking 05-diagram as completed
# ============================================================================

set -e
PROJECT_PATH="${1:-.}"
cd "$PROJECT_PATH/04-ui-flow"

echo ""
echo "🔍 Exit Validation: 05-diagram"
echo "==============================="
echo ""

ERRORS=0

# Get actual screen count
IPAD_COUNT=$(find . -name "SCR-*.html" -not -path "./iphone/*" -not -path "./docs/*" 2>/dev/null | wc -l | tr -d ' ')

# ============================================================================
# 1. Diagram Files Exist
# ============================================================================
echo "📄 [1/3] Diagram Files..."

[ -f "docs/ui-flow-diagram-ipad.html" ] && echo "  ✅ ui-flow-diagram-ipad.html" || { echo "  ❌ ui-flow-diagram-ipad.html missing"; ERRORS=$((ERRORS+1)); }
[ -f "docs/ui-flow-diagram-iphone.html" ] && echo "  ✅ ui-flow-diagram-iphone.html" || { echo "  ❌ ui-flow-diagram-iphone.html missing"; ERRORS=$((ERRORS+1)); }

# ============================================================================
# 2. Diagram Screen Count
# ============================================================================
echo ""
echo "📊 [2/3] Diagram Screen Count..."

if [ -f "docs/ui-flow-diagram-ipad.html" ]; then
  DIAGRAM_IPAD=$(grep -c 'onclick="openScreen' docs/ui-flow-diagram-ipad.html 2>/dev/null || echo "0")
  echo "  iPad Diagram screens: $DIAGRAM_IPAD"
  if [ "$DIAGRAM_IPAD" -ne "$IPAD_COUNT" ]; then
    echo "  ❌ Mismatch: Diagram=$DIAGRAM_IPAD, Actual=$IPAD_COUNT"
    ERRORS=$((ERRORS+1))
  else
    echo "  ✅ iPad Diagram count matches"
  fi
fi

if [ -f "docs/ui-flow-diagram-iphone.html" ]; then
  DIAGRAM_IPHONE=$(grep -c 'onclick="openScreen\|onclick="loadScreen' docs/ui-flow-diagram-iphone.html 2>/dev/null || echo "0")
  echo "  iPhone Diagram screens: $DIAGRAM_IPHONE"
  if [ "$DIAGRAM_IPHONE" -ne "$IPAD_COUNT" ]; then
    echo "  ❌ Mismatch: Diagram=$DIAGRAM_IPHONE, Actual=$IPAD_COUNT"
    ERRORS=$((ERRORS+1))
  else
    echo "  ✅ iPhone Diagram count matches"
  fi
fi

# ============================================================================
# 3. iframe src Path Validation
# ============================================================================
echo ""
echo "🔗 [3/3] iframe src Path Validation..."

SKILL_DIR="$HOME/.claude/skills/app-uiux-designer.skill"
if [ -f "$SKILL_DIR/templates/ui-flow/validate-iframe-src.js" ]; then
  node "$SKILL_DIR/templates/ui-flow/validate-iframe-src.js" . || {
    echo "  ❌ iframe src validation failed"
    ERRORS=$((ERRORS+1))
  }
else
  echo "  ⚠️ validate-iframe-src.js not found, manual check required"
fi

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "==============================="
if [ $ERRORS -eq 0 ]; then
  echo "✅ Exit Validation PASSED"
  echo ""
  echo "Diagrams are complete and valid"
  echo "Next step: 06-screenshot"
  exit 0
else
  echo "❌ Exit Validation FAILED ($ERRORS errors)"
  echo ""
  echo "Fix diagram issues before proceeding"
  exit 1
fi
