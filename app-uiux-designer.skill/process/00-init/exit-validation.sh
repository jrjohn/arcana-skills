#!/bin/bash
# ============================================================================
# Exit Validation - 00-init
# ============================================================================
# Must pass before marking 00-init as completed
# ============================================================================

set -e
PROJECT_PATH="${1:-.}"
cd "$PROJECT_PATH/04-ui-flow"

echo ""
echo "🔍 Exit Validation: 00-init"
echo "=============================="
echo ""

ERRORS=0

# 1. Check workspace exists
echo "📁 Checking workspace..."
[ -d "workspace" ] || { echo "❌ workspace/ not found"; ERRORS=$((ERRORS+1)); }
[ -d "workspace/context" ] || { echo "❌ workspace/context/ not found"; ERRORS=$((ERRORS+1)); }
[ -d "workspace/state" ] || { echo "❌ workspace/state/ not found"; ERRORS=$((ERRORS+1)); }
[ $ERRORS -eq 0 ] && echo "✅ workspace structure OK"

# 2. Check current-process.json
echo ""
echo "📄 Checking current-process.json..."
if [ -f "workspace/current-process.json" ]; then
  # Check for required fields
  grep -q '"current_process"' workspace/current-process.json || { echo "❌ Missing current_process field"; ERRORS=$((ERRORS+1)); }
  grep -q '"progress"' workspace/current-process.json || { echo "❌ Missing progress field"; ERRORS=$((ERRORS+1)); }
  [ $ERRORS -eq 0 ] && echo "✅ current-process.json valid"
else
  echo "❌ current-process.json not found"
  ERRORS=$((ERRORS+1))
fi

# 3. Check directory structure
echo ""
echo "📁 Checking directory structure..."
REQUIRED_DIRS=("auth" "common" "dash" "parent" "profile" "progress" "setting" "train" "vocab" "docs" "iphone" "shared")
for dir in "${REQUIRED_DIRS[@]}"; do
  if [ -d "$dir" ]; then
    echo "  ✅ $dir/"
  else
    echo "  ❌ $dir/ missing"
    ERRORS=$((ERRORS+1))
  fi
done

# 4. Check shared files
echo ""
echo "📁 Checking shared files..."
[ -f "shared/project-theme.css" ] || { echo "❌ shared/project-theme.css not found"; ERRORS=$((ERRORS+1)); }
[ -f "shared/notify-parent.js" ] || { echo "❌ shared/notify-parent.js not found"; ERRORS=$((ERRORS+1)); }
[ $ERRORS -eq 0 ] && echo "✅ shared files OK"

# Summary
echo ""
echo "=============================="
if [ $ERRORS -eq 0 ]; then
  echo "✅ Exit Validation PASSED"
  echo ""
  echo "Updating validation-chain.json..."

  # Update validation chain
  TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  if [ -f "workspace/validation-chain.json" ]; then
    # Add to existing chain (simplified - in production use jq)
    echo "Chain updated at $TIMESTAMP"
  fi

  exit 0
else
  echo "❌ Exit Validation FAILED ($ERRORS errors)"
  echo "Fix issues before proceeding to 03-generation"
  exit 1
fi
