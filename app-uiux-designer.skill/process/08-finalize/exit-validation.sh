#!/bin/bash
# ============================================================================
# Exit Validation - 08-finalize
# ============================================================================
# Final validation before marking the entire UI Flow phase as complete
# ============================================================================

set -e
PROJECT_PATH="${1:-.}"
cd "$PROJECT_PATH"

echo ""
echo "🔍 Exit Validation: 08-finalize (FINAL)"
echo "========================================"
echo ""

ERRORS=0
WARNINGS=0

# ============================================================================
# 1. All Previous Validations Passed
# ============================================================================
echo "📋 [1/5] Validation Chain..."

if [ -f "04-ui-flow/workspace/validation-chain.json" ]; then
  CHAIN_COUNT=$(grep -c '"result": "PASSED"' 04-ui-flow/workspace/validation-chain.json 2>/dev/null || echo "0")
  echo "  Passed validations: $CHAIN_COUNT"
  if [ "$CHAIN_COUNT" -lt 5 ]; then
    echo "  ⚠️ Some validation steps may be missing"
    WARNINGS=$((WARNINGS+1))
  else
    echo "  ✅ All major validations passed"
  fi
else
  echo "  ⚠️ validation-chain.json not found"
  WARNINGS=$((WARNINGS+1))
fi

# ============================================================================
# 2. Screen Count Summary
# ============================================================================
echo ""
echo "📊 [2/5] Screen Count Summary..."

IPAD_HTML=$(find 04-ui-flow -name "SCR-*.html" -not -path "*/iphone/*" -not -path "*/docs/*" 2>/dev/null | wc -l | tr -d ' ')
IPHONE_HTML=$(find 04-ui-flow/iphone -name "SCR-*.html" 2>/dev/null | wc -l | tr -d ' ')
IPAD_PNG=$(find 04-ui-flow/screenshots/ipad -name "*.png" 2>/dev/null | wc -l | tr -d ' ')
IPHONE_PNG=$(find 04-ui-flow/screenshots/iphone -name "*.png" 2>/dev/null | wc -l | tr -d ' ')

echo "  iPad HTML:     $IPAD_HTML"
echo "  iPhone HTML:   $IPHONE_HTML"
echo "  iPad PNG:      $IPAD_PNG"
echo "  iPhone PNG:    $IPHONE_PNG"

if [ "$IPAD_HTML" -ne "$IPHONE_HTML" ]; then
  echo "  ❌ HTML count mismatch"
  ERRORS=$((ERRORS+1))
fi

if [ "$IPAD_PNG" -lt "$IPAD_HTML" ] || [ "$IPHONE_PNG" -lt "$IPHONE_HTML" ]; then
  echo "  ❌ Screenshot count incomplete"
  ERRORS=$((ERRORS+1))
fi

# ============================================================================
# 3. Documentation Complete
# ============================================================================
echo ""
echo "📄 [3/5] Documentation..."

[ -f "01-requirements/SRS-"*".md" ] && echo "  ✅ SRS.md" || { echo "  ❌ SRS.md missing"; ERRORS=$((ERRORS+1)); }
[ -f "02-design/SDD-"*".md" ] && echo "  ✅ SDD.md" || { echo "  ❌ SDD.md missing"; ERRORS=$((ERRORS+1)); }
[ -f "01-requirements/SRS-"*".docx" ] && echo "  ✅ SRS.docx" || { echo "  ❌ SRS.docx missing"; ERRORS=$((ERRORS+1)); }
[ -f "02-design/SDD-"*".docx" ] && echo "  ✅ SDD.docx" || { echo "  ❌ SDD.docx missing"; ERRORS=$((ERRORS+1)); }

# ============================================================================
# 4. UI Flow Viewer
# ============================================================================
echo ""
echo "🖥️ [4/5] UI Flow Viewer..."

[ -f "04-ui-flow/index.html" ] && echo "  ✅ index.html" || { echo "  ❌ index.html missing"; ERRORS=$((ERRORS+1)); }
[ -f "04-ui-flow/device-preview.html" ] && echo "  ✅ device-preview.html" || { echo "  ❌ device-preview.html missing"; ERRORS=$((ERRORS+1)); }
[ -f "04-ui-flow/docs/ui-flow-diagram-ipad.html" ] && echo "  ✅ ui-flow-diagram-ipad.html" || { echo "  ❌ ui-flow-diagram-ipad.html missing"; ERRORS=$((ERRORS+1)); }
[ -f "04-ui-flow/docs/ui-flow-diagram-iphone.html" ] && echo "  ✅ ui-flow-diagram-iphone.html" || { echo "  ❌ ui-flow-diagram-iphone.html missing"; ERRORS=$((ERRORS+1)); }

# ============================================================================
# 5. Process State
# ============================================================================
echo ""
echo "📍 [5/5] Process State..."

if [ -f "04-ui-flow/workspace/current-process.json" ]; then
  echo "  ✅ current-process.json exists"
  # Mark as completed
  CURRENT=$(grep -o '"current_process": "[^"]*"' 04-ui-flow/workspace/current-process.json | cut -d'"' -f4)
  echo "  Current node: $CURRENT"
else
  echo "  ❌ current-process.json missing"
  ERRORS=$((ERRORS+1))
fi

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "========================================"
echo "Final Summary:"
echo "  Total Screens: $IPAD_HTML"
echo "  Errors: $ERRORS"
echo "  Warnings: $WARNINGS"
echo ""

if [ $ERRORS -eq 0 ]; then
  echo "✅ =============================================="
  echo "✅  UI FLOW PHASE COMPLETE!"
  echo "✅ =============================================="
  echo ""
  echo "All validations passed. The UI Flow is ready for:"
  echo "  - Development handoff"
  echo "  - Stakeholder review"
  echo "  - User testing"
  echo ""
  echo "Deliverables:"
  echo "  - 04-ui-flow/index.html (Interactive viewer)"
  echo "  - 04-ui-flow/screenshots/ (Static images)"
  echo "  - 01-requirements/SRS.docx"
  echo "  - 02-design/SDD.docx"
  exit 0
else
  echo "❌ Exit Validation FAILED ($ERRORS errors)"
  echo ""
  echo "Please fix the above issues to complete the UI Flow phase"
  exit 1
fi
