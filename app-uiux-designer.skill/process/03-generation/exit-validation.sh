#!/bin/bash
# ============================================================================
# Exit Validation - 03-generation (CRITICAL)
# ============================================================================
# Must pass before marking 03-generation as completed
# This is one of the most important validations!
# ============================================================================

set -e
PROJECT_PATH="${1:-.}"
cd "$PROJECT_PATH/04-ui-flow"

echo ""
echo "🔍 Exit Validation: 03-generation (CRITICAL)"
echo "=============================================="
echo ""

ERRORS=0
WARNINGS=0

# ============================================================================
# 1. Screen Count Validation
# ============================================================================
echo "📊 [1/5] Screen Count..."

IPAD_COUNT=$(find . -name "SCR-*.html" -not -path "./iphone/*" -not -path "./docs/*" 2>/dev/null | wc -l | tr -d ' ')
IPHONE_COUNT=$(find ./iphone -name "SCR-*.html" 2>/dev/null | wc -l | tr -d ' ')

echo "  iPad screens:  $IPAD_COUNT"
echo "  iPhone screens: $IPHONE_COUNT"

if [ "$IPAD_COUNT" -eq 0 ]; then
  echo "  ❌ No iPad screens found!"
  ERRORS=$((ERRORS+1))
elif [ "$IPAD_COUNT" -ne "$IPHONE_COUNT" ]; then
  echo "  ❌ iPad/iPhone count mismatch!"
  ERRORS=$((ERRORS+1))
else
  echo "  ✅ Screen counts match"
fi

# ============================================================================
# 2. onclick Coverage (CRITICAL)
# ============================================================================
echo ""
echo "🔘 [2/5] onclick Coverage (CRITICAL)..."

EMPTY_ONCLICK=0
ALERT_ONCLICK=0

# Check for empty onclick
for file in $(find . -name "SCR-*.html" -not -path "./iphone/*" -not -path "./docs/*"); do
  EMPTY=$(grep -c 'onclick=""' "$file" 2>/dev/null || echo "0")
  EMPTY_ONCLICK=$((EMPTY_ONCLICK + EMPTY))
done

# Check for alert placeholders
for file in $(find . -name "SCR-*.html" -not -path "./iphone/*" -not -path "./docs/*"); do
  ALERTS=$(grep -c "onclick=\"alert(" "$file" 2>/dev/null || echo "0")
  ALERT_ONCLICK=$((ALERT_ONCLICK + ALERTS))
done

echo "  Empty onclick:   $EMPTY_ONCLICK"
echo "  Alert onclick:   $ALERT_ONCLICK"

if [ "$EMPTY_ONCLICK" -gt 0 ]; then
  echo "  ❌ Found $EMPTY_ONCLICK empty onclick handlers!"
  ERRORS=$((ERRORS+1))
fi

if [ "$ALERT_ONCLICK" -gt 0 ]; then
  echo "  ❌ Found $ALERT_ONCLICK alert placeholder onclick handlers!"
  ERRORS=$((ERRORS+1))
fi

if [ "$EMPTY_ONCLICK" -eq 0 ] && [ "$ALERT_ONCLICK" -eq 0 ]; then
  echo "  ✅ No forbidden onclick patterns"
fi

# ============================================================================
# 3. index.html Validation (CRITICAL)
# ============================================================================
echo ""
echo "📄 [3/5] index.html Validation (CRITICAL)..."

if [ -f "index.html" ]; then
  # Check for placeholder text
  if grep -q "尚未產生畫面" index.html; then
    echo "  ❌ index.html contains placeholder '尚未產生畫面'"
    ERRORS=$((ERRORS+1))
  else
    echo "  ✅ No placeholder text"
  fi

  # Check for unreplaced template variables
  if grep -q '{{' index.html; then
    echo "  ❌ index.html contains unreplaced template variables"
    ERRORS=$((ERRORS+1))
  else
    echo "  ✅ No unreplaced variables"
  fi

  # Check coverage display
  COVERAGE=$(grep -oE 'id="coverage-rate">[^<]+' index.html | sed 's/.*>//' || echo "0%")
  if [ "$COVERAGE" = "0%" ]; then
    echo "  ❌ index.html shows 0% coverage"
    ERRORS=$((ERRORS+1))
  else
    echo "  ✅ Coverage displayed: $COVERAGE"
  fi

  # Check screen count display
  DISPLAYED_IPAD=$(grep -oE 'id="ipad-count">[^<]+' index.html | sed 's/.*>//' || echo "0")
  if [ "$DISPLAYED_IPAD" = "0" ]; then
    echo "  ❌ index.html shows iPad count as 0"
    ERRORS=$((ERRORS+1))
  elif [ "$DISPLAYED_IPAD" != "$IPAD_COUNT" ]; then
    echo "  ⚠️ Displayed count ($DISPLAYED_IPAD) != actual ($IPAD_COUNT)"
    WARNINGS=$((WARNINGS+1))
  else
    echo "  ✅ iPad count correct: $DISPLAYED_IPAD"
  fi

  # Check module cards exist
  MODULE_CARDS=$(grep -c 'module-card' index.html || echo "0")
  if [ "$MODULE_CARDS" -lt 5 ]; then
    echo "  ❌ Only $MODULE_CARDS module cards found (expected 9+)"
    ERRORS=$((ERRORS+1))
  else
    echo "  ✅ Module cards: $MODULE_CARDS"
  fi
else
  echo "  ❌ index.html not found!"
  ERRORS=$((ERRORS+1))
fi

# ============================================================================
# 4. device-preview.html Validation
# ============================================================================
echo ""
echo "📱 [4/5] device-preview.html Validation..."

if [ -f "device-preview.html" ]; then
  SIDEBAR_COUNT=$(grep -c 'screen-item\|loadScreen' device-preview.html 2>/dev/null || echo "0")
  echo "  Sidebar items: $SIDEBAR_COUNT"

  if [ "$SIDEBAR_COUNT" -lt "$IPAD_COUNT" ]; then
    echo "  ⚠️ Sidebar may be incomplete"
    WARNINGS=$((WARNINGS+1))
  else
    echo "  ✅ Sidebar populated"
  fi
else
  echo "  ❌ device-preview.html not found!"
  ERRORS=$((ERRORS+1))
fi

# ============================================================================
# 5. Diagram Files
# ============================================================================
echo ""
echo "📊 [5/5] Diagram Files..."

[ -f "docs/ui-flow-diagram-ipad.html" ] && echo "  ✅ ui-flow-diagram-ipad.html" || { echo "  ❌ ui-flow-diagram-ipad.html missing"; ERRORS=$((ERRORS+1)); }
[ -f "docs/ui-flow-diagram-iphone.html" ] && echo "  ✅ ui-flow-diagram-iphone.html" || { echo "  ❌ ui-flow-diagram-iphone.html missing"; ERRORS=$((ERRORS+1)); }

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "=============================================="
echo "Summary:"
echo "  Screens: iPad=$IPAD_COUNT, iPhone=$IPHONE_COUNT"
echo "  Errors: $ERRORS"
echo "  Warnings: $WARNINGS"
echo ""

if [ $ERRORS -eq 0 ]; then
  echo "✅ Exit Validation PASSED"
  echo ""
  echo "Safe to mark 03-generation as completed"
  echo "Next step: 04-validation"
  exit 0
else
  echo "❌ Exit Validation FAILED"
  echo ""
  echo "🚨 DO NOT proceed to next step!"
  echo "Fix the above errors first."
  exit 1
fi
