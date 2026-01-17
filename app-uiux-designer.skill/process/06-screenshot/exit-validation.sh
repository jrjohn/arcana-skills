#!/bin/bash
# ============================================================================
# Exit Validation - 06-screenshot
# ============================================================================
# Must pass before marking 06-screenshot as completed
# ============================================================================

set -e
PROJECT_PATH="${1:-.}"
cd "$PROJECT_PATH/04-ui-flow"

echo ""
echo "🔍 Exit Validation: 06-screenshot"
echo "=================================="
echo ""

ERRORS=0

# Get expected screen count
IPAD_COUNT=$(find . -name "SCR-*.html" -not -path "./iphone/*" -not -path "./docs/*" 2>/dev/null | wc -l | tr -d ' ')

# ============================================================================
# 1. Screenshot Directories Exist
# ============================================================================
echo "📁 [1/3] Screenshot Directories..."

[ -d "screenshots/ipad" ] && echo "  ✅ screenshots/ipad/" || { echo "  ❌ screenshots/ipad/ missing"; ERRORS=$((ERRORS+1)); }
[ -d "screenshots/iphone" ] && echo "  ✅ screenshots/iphone/" || { echo "  ❌ screenshots/iphone/ missing"; ERRORS=$((ERRORS+1)); }

# ============================================================================
# 2. Screenshot Count
# ============================================================================
echo ""
echo "📸 [2/3] Screenshot Count..."

if [ -d "screenshots/ipad" ]; then
  IPAD_SCREENSHOTS=$(find screenshots/ipad -name "SCR-*.png" 2>/dev/null | wc -l | tr -d ' ')
  echo "  iPad screenshots: $IPAD_SCREENSHOTS"
  if [ "$IPAD_SCREENSHOTS" -ne "$IPAD_COUNT" ]; then
    echo "  ❌ Missing iPad screenshots: expected $IPAD_COUNT, found $IPAD_SCREENSHOTS"
    ERRORS=$((ERRORS+1))
  else
    echo "  ✅ iPad screenshots complete"
  fi
else
  IPAD_SCREENSHOTS=0
fi

if [ -d "screenshots/iphone" ]; then
  IPHONE_SCREENSHOTS=$(find screenshots/iphone -name "SCR-*.png" 2>/dev/null | wc -l | tr -d ' ')
  echo "  iPhone screenshots: $IPHONE_SCREENSHOTS"
  if [ "$IPHONE_SCREENSHOTS" -ne "$IPAD_COUNT" ]; then
    echo "  ❌ Missing iPhone screenshots: expected $IPAD_COUNT, found $IPHONE_SCREENSHOTS"
    ERRORS=$((ERRORS+1))
  else
    echo "  ✅ iPhone screenshots complete"
  fi
else
  IPHONE_SCREENSHOTS=0
fi

# ============================================================================
# 3. Screenshot File Size Check (detect empty/broken screenshots)
# ============================================================================
echo ""
echo "📏 [3/3] Screenshot File Size Check..."

SMALL_FILES=0
for file in screenshots/ipad/*.png screenshots/iphone/*.png 2>/dev/null; do
  if [ -f "$file" ]; then
    SIZE=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "0")
    if [ "$SIZE" -lt 1000 ]; then
      echo "  ⚠️ Small file: $file ($SIZE bytes)"
      SMALL_FILES=$((SMALL_FILES+1))
    fi
  fi
done

if [ "$SMALL_FILES" -gt 0 ]; then
  echo "  ⚠️ Found $SMALL_FILES potentially broken screenshots"
else
  echo "  ✅ All screenshots have valid file sizes"
fi

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "=================================="
echo "Summary:"
echo "  Expected: $IPAD_COUNT screens"
echo "  iPad screenshots: $IPAD_SCREENSHOTS"
echo "  iPhone screenshots: $IPHONE_SCREENSHOTS"
echo ""

if [ $ERRORS -eq 0 ]; then
  echo "✅ Exit Validation PASSED"
  echo ""
  echo "All screenshots generated successfully"
  echo "Next step: 07-feedback (回補 SDD/SRS)"
  exit 0
else
  echo "❌ Exit Validation FAILED ($ERRORS errors)"
  echo ""
  echo "Regenerate missing screenshots before proceeding"
  exit 1
fi
