#!/usr/bin/env bash
#
# install.sh — 1-Click Installer for claude-antigravity-sync skill & bridge tools
#

set -e

echo "=== Installing claude-antigravity-sync Skill & CLI Tools ==="

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ARCHIVE_DIR="$HOME/antigravity-archive"
BIN_DIR="$HOME/bin"
SKILL_TARGET="$HOME/.gemini/antigravity/builtin/skills/claude-antigravity-sync"
LAUNCHD_PLIST="$HOME/Library/LaunchAgents/com.jrjohn.antigravity-archive.plist"

# 1. Create target directories
mkdir -p "$ARCHIVE_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$SKILL_TARGET"
mkdir -p "$HOME/Library/LaunchAgents"

# 2. Copy Python scripts & shell wrappers
cp -R "$SCRIPT_DIR/scripts/"* "$ARCHIVE_DIR/"
chmod +x "$ARCHIVE_DIR/sync_all.sh"
chmod +x "$ARCHIVE_DIR/"*.py

# 3. Copy CLI executables to ~/bin
cp -R "$SCRIPT_DIR/bin/"* "$BIN_DIR/"
chmod +x "$BIN_DIR/agjobs"
chmod +x "$BIN_DIR/agload"

# 4. Copy Skill definition
cp "$SCRIPT_DIR/SKILL.md" "$SKILL_TARGET/SKILL.md"

# 5. Install & Load launchd daemon
if [ -f "$SCRIPT_DIR/scripts/com.jrjohn.antigravity-archive.plist" ]; then
    cp "$SCRIPT_DIR/scripts/com.jrjohn.antigravity-archive.plist" "$LAUNCHD_PLIST"
    launchctl unload "$LAUNCHD_PLIST" 2>/dev/null || true
    launchctl load "$LAUNCHD_PLIST"
    echo "✓ Background Launchd Daemon loaded: com.jrjohn.antigravity-archive"
fi

echo "========================================================="
echo "✓ Installation Complete!"
echo "  - CLI Tools installed to: $BIN_DIR (agjobs, agload)"
echo "  - Sync Scripts installed to: $ARCHIVE_DIR"
echo "  - Skill installed to: $SKILL_TARGET"
echo ""
echo "Try running: agjobs"
echo "========================================================="
