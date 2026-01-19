#!/bin/bash
# UI Flow Project Initializer
# Usage: ./init-project.sh <project-name> <project-icon> <total-screens> [project-description]
#
# This script replaces all {{VARIABLE}} placeholders in template files
# with project-specific values.

set -e

# ==================== Parameter Parsing ====================

PROJECT_NAME=${1:-"MyProject"}
PROJECT_ICON=${2:-"📱"}
TOTAL_SCREENS=${3:-"20"}
PROJECT_DESCRIPTION=${4:-""}

# Derived values
PROJECT_ID=$(echo "$PROJECT_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd '[:alnum:]-')
DATE=$(date +%Y-%m-%d)

# Initial values (will be updated by 03-generation and 05-diagram)
COVERAGE="0%"
MODULE_COUNT="0"
IPAD_COUNT="0"
IPHONE_COUNT="0"

# ==================== Header ====================

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           UI Flow Project Initializer v2.0                   ║"
echo "║           app-uiux-designer.skill                            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📋 Project Configuration:"
echo "   Name:        $PROJECT_NAME"
echo "   Icon:        $PROJECT_ICON"
echo "   ID:          $PROJECT_ID"
echo "   Screens:     $TOTAL_SCREENS"
echo "   Description: ${PROJECT_DESCRIPTION:-'(none)'}"
echo "   Date:        $DATE"
echo ""

# ==================== Pre-checks ====================

echo "🔍 Pre-checks..."

# Check if we're in the right directory
if [ ! -f "index.html" ]; then
    echo "❌ Error: index.html not found."
    echo "   Please run this script from the 04-ui-flow directory."
    echo "   Current directory: $(pwd)"
    exit 1
fi

# Check for required files
REQUIRED_FILES=(
    "index.html"
    "device-preview.html"
    "docs/ui-flow-diagram.html"
    "shared/project-theme.css"
)

MISSING=0
for f in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$f" ]; then
        echo "   ❌ Missing: $f"
        MISSING=1
    fi
done

if [ $MISSING -eq 1 ]; then
    echo ""
    echo "❌ Error: Some required files are missing."
    echo "   Did you run: cp -r ~/.claude/skills/app-uiux-designer.skill/templates/ui-flow/* ./"
    exit 1
fi

echo "   ✅ All required files present"
echo ""

# ==================== Variable Replacement ====================

echo "📝 Replacing template variables..."

# Function to replace variables in a file
replace_vars() {
    local file=$1
    if [ -f "$file" ]; then
        # Use temporary file for safety
        local tmp=$(mktemp)

        sed -e "s|{{PROJECT_NAME}}|$PROJECT_NAME|g" \
            -e "s|{{PROJECT_ID}}|$PROJECT_ID|g" \
            -e "s|{{PROJECT_ICON}}|$PROJECT_ICON|g" \
            -e "s|{{PROJECT_DESCRIPTION}}|$PROJECT_DESCRIPTION|g" \
            -e "s|{{TOTAL_SCREENS}}|$TOTAL_SCREENS|g" \
            -e "s|{{COVERAGE}}|$COVERAGE|g" \
            -e "s|{{MODULE_COUNT}}|$MODULE_COUNT|g" \
            -e "s|{{IPAD_COUNT}}|$IPAD_COUNT|g" \
            -e "s|{{IPHONE_COUNT}}|$IPHONE_COUNT|g" \
            -e "s|{{GENERATED_DATE}}|$DATE|g" \
            "$file" > "$tmp"

        mv "$tmp" "$file"
        echo "   ✅ $file"
    fi
}

# Root HTML files
replace_vars "index.html"
replace_vars "device-preview.html"

# Docs HTML files
for f in docs/*.html; do
    [ -f "$f" ] && replace_vars "$f"
done

# Shared CSS files
for f in shared/*.css; do
    [ -f "$f" ] && replace_vars "$f"
done

# Shared JS files
for f in shared/*.js; do
    [ -f "$f" ] && replace_vars "$f"
done

echo ""

# ==================== Directory Structure ====================

echo "📁 Creating directory structure..."

# Standard modules (all App types)
mkdir -p auth       # Authentication
mkdir -p onboard    # Onboarding
mkdir -p home       # Home/Landing
mkdir -p dash       # Dashboard
mkdir -p feature    # Generic feature module
mkdir -p profile    # User profile
mkdir -p setting    # Settings
mkdir -p report     # Reports/Analytics

# Extended modules (project-specific)
mkdir -p vocab      # Education: Vocabulary
mkdir -p train      # Education: Training
mkdir -p progress   # Education: Progress
mkdir -p parent     # Education: Parent controls
mkdir -p cart       # E-commerce: Shopping cart
mkdir -p product    # E-commerce: Products
mkdir -p social     # Social: Community

# Output directories
mkdir -p iphone
mkdir -p screenshots/ipad
mkdir -p screenshots/iphone

# Workspace
mkdir -p workspace/context
mkdir -p workspace/state

echo "   ✅ Module directories created"
echo ""

# ==================== Verification ====================

echo "🔍 Verification..."

# Check index.html
INDEX_LINES=$(wc -l < index.html | tr -d ' ')
if [ "$INDEX_LINES" -ge 500 ]; then
    echo "   ✅ index.html: $INDEX_LINES lines (>= 500)"
else
    echo "   ⚠️  index.html: $INDEX_LINES lines (should be >= 500)"
fi

# Check device-preview.html
DEVICE_PREVIEW_LINES=$(wc -l < device-preview.html | tr -d ' ')
if [ "$DEVICE_PREVIEW_LINES" -ge 600 ]; then
    echo "   ✅ device-preview.html: $DEVICE_PREVIEW_LINES lines (>= 600)"
else
    echo "   ⚠️  device-preview.html: $DEVICE_PREVIEW_LINES lines (should be >= 600)"
fi

# Check ui-flow-diagram.html
if [ -f "docs/ui-flow-diagram.html" ]; then
    DIAGRAM_LINES=$(wc -l < docs/ui-flow-diagram.html | tr -d ' ')
    if [ "$DIAGRAM_LINES" -ge 300 ]; then
        echo "   ✅ docs/ui-flow-diagram.html: $DIAGRAM_LINES lines (>= 300)"
    else
        echo "   ⚠️  docs/ui-flow-diagram.html: $DIAGRAM_LINES lines (should be >= 300)"
    fi
fi

# Check for remaining variables
REMAINING_INDEX=$(grep -c '{{' index.html 2>/dev/null || echo "0")
REMAINING_DEVICE=$(grep -c '{{' device-preview.html 2>/dev/null || echo "0")
REMAINING_DIAGRAM=$(grep -c '{{' docs/ui-flow-diagram.html 2>/dev/null || echo "0")
TOTAL_REMAINING=$((REMAINING_INDEX + REMAINING_DEVICE + REMAINING_DIAGRAM))

if [ "$TOTAL_REMAINING" -eq 0 ]; then
    echo "   ✅ No remaining {{VARIABLES}} in HTML files"
else
    echo "   ⚠️  $TOTAL_REMAINING remaining {{VARIABLES}} found:"
    [ "$REMAINING_INDEX" -gt 0 ] && echo "      - index.html: $REMAINING_INDEX"
    [ "$REMAINING_DEVICE" -gt 0 ] && echo "      - device-preview.html: $REMAINING_DEVICE"
    [ "$REMAINING_DIAGRAM" -gt 0 ] && echo "      - docs/ui-flow-diagram.html: $REMAINING_DIAGRAM"
fi

# Check scripts
SCRIPT_COUNT=$(ls -1 scripts/*.sh 2>/dev/null | wc -l | tr -d ' ')
if [ "$SCRIPT_COUNT" -ge 3 ]; then
    echo "   ✅ scripts/: $SCRIPT_COUNT shell scripts"
else
    echo "   ⚠️  scripts/: $SCRIPT_COUNT shell scripts (should be >= 3)"
fi

# Check JS files
for f in capture-screenshots.js validate-navigation.js; do
    if [ -f "$f" ]; then
        echo "   ✅ $f present"
    else
        echo "   ❌ $f missing!"
    fi
done

echo ""

# ==================== Summary ====================

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    Initialization Complete!                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📁 Project structure created at: $(pwd)"
echo ""
echo "📋 Next steps:"
echo "   1. Create workspace/current-process.json (Claude will do this)"
echo "   2. Enter 01-discovery or 02-planning process"
echo "   3. Generate screens in 03-generation"
echo "   4. Validate 100% coverage in 04-validation"
echo "   5. Generate diagram in 05-diagram"
echo ""
echo "🔧 Useful commands:"
echo "   - Convert iPad to iPhone: bash scripts/convert-to-iphone.sh"
echo "   - Update index counts:    bash scripts/update-index-counts.sh"
echo "   - Validate navigation:    node validate-navigation.js"
echo "   - Capture screenshots:    node capture-screenshots.js"
echo ""
