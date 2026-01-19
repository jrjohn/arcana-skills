#!/bin/bash
# ============================================================================
# Exit Validation - 04-validation
# ============================================================================
# Must pass before marking 04-validation as completed
# ============================================================================

set -e
PROJECT_PATH="${1:-.}"
cd "$PROJECT_PATH/04-ui-flow"

echo ""
echo "🔍 Exit Validation: 04-validation"
echo "==================================="
echo ""

ERRORS=0

# ============================================================================
# 1. Navigation Validation (use existing script)
# ============================================================================
echo "🔗 [1/3] Navigation Validation..."

SKILL_DIR="$HOME/.claude/skills/app-uiux-designer.skill"
if [ -f "$SKILL_DIR/templates/ui-flow/validate-navigation.js" ]; then
  node "$SKILL_DIR/templates/ui-flow/validate-navigation.js" . || {
    echo "  ❌ Navigation validation failed"
    ERRORS=$((ERRORS+1))
  }
else
  echo "  ⚠️ validate-navigation.js not found, manual check required"
fi

# ============================================================================
# 2. Consistency Validation
# ============================================================================
echo ""
echo "🔄 [2/3] Consistency Validation..."

if [ -f "$SKILL_DIR/templates/ui-flow/validate-consistency.js" ]; then
  node "$SKILL_DIR/templates/ui-flow/validate-consistency.js" . || {
    echo "  ❌ Consistency validation failed"
    ERRORS=$((ERRORS+1))
  }
else
  echo "  ⚠️ validate-consistency.js not found, manual check required"
fi

# ============================================================================
# 3. Zero Alert Check
# ============================================================================
echo ""
echo "🚫 [3/3] Zero Alert Check..."

ALERT_COUNT=0
for file in $(find . -name "SCR-*.html" -not -path "./iphone/*" -not -path "./docs/*"); do
  ALERTS=$(grep -c "onclick=\"alert(" "$file" 2>/dev/null || echo "0")
  ALERT_COUNT=$((ALERT_COUNT + ALERTS))
done

echo "  Alert onclick found: $ALERT_COUNT"

if [ "$ALERT_COUNT" -gt 0 ]; then
  echo "  ❌ Alert placeholders must be replaced!"
  echo "  Files with alerts:"
  grep -l "onclick=\"alert(" $(find . -name "SCR-*.html" -not -path "./iphone/*" -not -path "./docs/*") 2>/dev/null || true
  ERRORS=$((ERRORS+1))
else
  echo "  ✅ No alert placeholders"
fi

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "==================================="
if [ $ERRORS -eq 0 ]; then
  echo "✅ Exit Validation PASSED"
  echo ""
  echo "Navigation is 100% valid"
  echo "Next step: 05-diagram"
  exit 0
else
  echo "❌ Exit Validation FAILED ($ERRORS errors)"
  echo ""
  echo "Fix navigation issues before proceeding"
  exit 1
fi
