#!/bin/bash
# ============================================================================
# Exit Validation - 07-feedback
# ============================================================================
# Must pass before marking 07-feedback as completed
# ============================================================================

set -e
PROJECT_PATH="${1:-.}"
cd "$PROJECT_PATH"

echo ""
echo "🔍 Exit Validation: 07-feedback"
echo "================================"
echo ""

ERRORS=0

# Find SDD file
SDD_FILE=$(ls 02-design/SDD-*.md 2>/dev/null | head -1)
SRS_FILE=$(ls 01-requirements/SRS-*.md 2>/dev/null | head -1)

# Get expected screen count
SCREEN_COUNT=$(find 04-ui-flow -name "SCR-*.html" -not -path "*/iphone/*" -not -path "*/docs/*" 2>/dev/null | wc -l | tr -d ' ')

# ============================================================================
# 1. SDD UI 原型參考
# ============================================================================
echo "📄 [1/4] SDD UI 原型參考..."

if [ -f "$SDD_FILE" ]; then
  # Count iPad image references
  IPAD_REF=$(grep -c "images/ipad/SCR-.*\.png" "$SDD_FILE" 2>/dev/null || echo "0")
  # Count iPhone image references
  IPHONE_REF=$(grep -c "images/iphone/SCR-.*\.png" "$SDD_FILE" 2>/dev/null || echo "0")

  echo "  Expected screens: $SCREEN_COUNT"
  echo "  iPad references:  $IPAD_REF"
  echo "  iPhone references: $IPHONE_REF"

  if [ "$IPAD_REF" -lt "$SCREEN_COUNT" ]; then
    echo "  ❌ Missing iPad image references in SDD"
    ERRORS=$((ERRORS+1))
  else
    echo "  ✅ iPad references complete"
  fi

  if [ "$IPHONE_REF" -lt "$SCREEN_COUNT" ]; then
    echo "  ❌ Missing iPhone image references in SDD"
    ERRORS=$((ERRORS+1))
  else
    echo "  ✅ iPhone references complete"
  fi
else
  echo "  ❌ SDD file not found"
  ERRORS=$((ERRORS+1))
fi

# ============================================================================
# 2. Image Files Exist
# ============================================================================
echo ""
echo "🖼️ [2/4] Image Files..."

if [ -d "02-design/images/ipad" ]; then
  IPAD_IMAGES=$(find 02-design/images/ipad -name "SCR-*.png" 2>/dev/null | wc -l | tr -d ' ')
  echo "  iPad images: $IPAD_IMAGES"
  if [ "$IPAD_IMAGES" -lt "$SCREEN_COUNT" ]; then
    echo "  ❌ Missing iPad images"
    ERRORS=$((ERRORS+1))
  fi
else
  echo "  ❌ 02-design/images/ipad/ not found"
  ERRORS=$((ERRORS+1))
fi

if [ -d "02-design/images/iphone" ]; then
  IPHONE_IMAGES=$(find 02-design/images/iphone -name "SCR-*.png" 2>/dev/null | wc -l | tr -d ' ')
  echo "  iPhone images: $IPHONE_IMAGES"
  if [ "$IPHONE_IMAGES" -lt "$SCREEN_COUNT" ]; then
    echo "  ❌ Missing iPhone images"
    ERRORS=$((ERRORS+1))
  fi
else
  echo "  ❌ 02-design/images/iphone/ not found"
  ERRORS=$((ERRORS+1))
fi

# ============================================================================
# 3. SRS Screen References
# ============================================================================
echo ""
echo "📋 [3/4] SRS Screen References..."

if [ -f "$SRS_FILE" ]; then
  if grep -q "Screen References\|畫面參考" "$SRS_FILE"; then
    echo "  ✅ Screen References section found"
  else
    echo "  ⚠️ Screen References section not found (optional)"
  fi
else
  echo "  ⚠️ SRS file not found (optional)"
fi

# ============================================================================
# 4. DOCX Files Generated
# ============================================================================
echo ""
echo "📄 [4/4] DOCX Files..."

SDD_DOCX=$(ls 02-design/SDD-*.docx 2>/dev/null | head -1)
SRS_DOCX=$(ls 01-requirements/SRS-*.docx 2>/dev/null | head -1)

if [ -f "$SDD_DOCX" ]; then
  SIZE=$(stat -f%z "$SDD_DOCX" 2>/dev/null || stat -c%s "$SDD_DOCX" 2>/dev/null || echo "0")
  echo "  ✅ SDD.docx exists ($SIZE bytes)"
else
  echo "  ❌ SDD.docx not found"
  ERRORS=$((ERRORS+1))
fi

if [ -f "$SRS_DOCX" ]; then
  SIZE=$(stat -f%z "$SRS_DOCX" 2>/dev/null || stat -c%s "$SRS_DOCX" 2>/dev/null || echo "0")
  echo "  ✅ SRS.docx exists ($SIZE bytes)"
else
  echo "  ❌ SRS.docx not found"
  ERRORS=$((ERRORS+1))
fi

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "================================"
if [ $ERRORS -eq 0 ]; then
  echo "✅ Exit Validation PASSED"
  echo ""
  echo "SDD/SRS feedback complete"
  echo "DOCX files generated"
  echo "Next step: 08-finalize"
  exit 0
else
  echo "❌ Exit Validation FAILED ($ERRORS errors)"
  echo ""
  echo "Complete feedback and DOCX generation before proceeding"
  exit 1
fi
