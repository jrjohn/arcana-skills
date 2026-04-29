#!/usr/bin/env bash
#
# install.sh — Base installer for claude-session-archive (macOS / Linux).
#
# Builds the Rust binary `crs` (single ~5 MB self-contained binary, bundles
# SQLite + FTS5 + sqlite-vec) and wires up the 15-min ingest schedule.
#
# Steps:
#   1. Verify cargo is present (rustup needed)
#   2. mkdirs ~/claude-archive ~/bin
#   3. Copy crs source → cargo build --release
#   4. ~/bin/crs symlink + PATH on shell rc (zsh / bash / sh)
#   5. ~/.sqliterc tuning
#   6. Install gen-recent-context.sh
#   7. Schedule 15-min ingest:
#        macOS  → launchd plist
#        Linux  → crontab entry
#   8. Register SessionStart hook in ~/.claude/settings.json (needs jq)
#   9. First ingest run
#  10. Smoke test
#
# Idempotent: re-running rebuilds + re-points hooks safely.
#
# AFTER this: optionally run install-semantic.sh to add Ollama + bge-m3 for
# semantic vsearch. Pure FTS5 csearch works without it.

set -e

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARCHIVE_DIR="$HOME/claude-archive"
SRC_DIR="$ARCHIVE_DIR/crs"
BIN="$SRC_DIR/target/release/crs"
USER_BIN="$HOME/bin"
SETTINGS="$HOME/.claude/settings.json"
PLATFORM="$(uname -s)"

echo "==> install.sh — claude-session-archive base"
echo "    skill source: $SKILL_DIR"
echo "    archive dir:  $ARCHIVE_DIR"
echo "    crs binary:   $BIN"
echo "    platform:     $PLATFORM"

# 1. Sanity: cargo present
if ! command -v cargo >/dev/null 2>&1; then
    echo "!! cargo not found in PATH."
    echo "   Install Rust toolchain first:"
    echo "     curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
    echo "   Then re-run this script."
    exit 1
fi
echo "    cargo: $(cargo --version)"

# 2. mkdirs
mkdir -p "$ARCHIVE_DIR" "$USER_BIN"

# 3. Copy crs source into ~/claude-archive/crs/ + build
mkdir -p "$SRC_DIR/src"
cp "$SKILL_DIR/scripts/crs/Cargo.toml"  "$SRC_DIR/Cargo.toml"
cp "$SKILL_DIR/scripts/crs/Cargo.lock"  "$SRC_DIR/Cargo.lock" 2>/dev/null || true
cp "$SKILL_DIR/scripts/crs/src/main.rs" "$SRC_DIR/src/main.rs"
[ -f "$SKILL_DIR/scripts/crs/.gitignore" ] && cp "$SKILL_DIR/scripts/crs/.gitignore" "$SRC_DIR/.gitignore"

echo "==> cargo build --release  (first time ~2-5 min, deps cached afterwards)"
( cd "$SRC_DIR" && cargo build --release )
echo "    built: $(du -h "$BIN" | cut -f1) at $BIN"

# 4. Symlink to ~/bin/crs + ensure ~/bin on PATH
ln -sf "$BIN" "$USER_BIN/crs"
echo "    symlink: $USER_BIN/crs → $BIN"
case ":$PATH:" in
    *":$USER_BIN:"*) : ;;
    *)
        case "${SHELL##*/}" in
            zsh) RC="$HOME/.zshrc" ;;
            bash) RC="$HOME/.bashrc" ;;
            *) RC="$HOME/.profile" ;;
        esac
        if [ -f "$RC" ] && grep -qE '\$HOME/bin|"~/bin"' "$RC"; then
            echo "    PATH: ~/bin already referenced in $RC — no change"
        else
            printf '\n# claude-session-archive: ensure ~/bin on PATH for crs\nexport PATH="$HOME/bin:$PATH"\n' >> "$RC"
            echo "    PATH: appended export to $RC (open a new shell to pick up)"
        fi
        ;;
esac

# 5. ~/.sqliterc tuning
cp "$SKILL_DIR/scripts/sqliterc.template" "$HOME/.sqliterc"
echo "    sqliterc: $HOME/.sqliterc"

# 6. gen-recent-context.sh
cp "$SKILL_DIR/scripts/gen-recent-context.sh" "$ARCHIVE_DIR/gen-recent-context.sh"
chmod +x "$ARCHIVE_DIR/gen-recent-context.sh"
echo "    gen-recent-context.sh installed"

# 7. Schedule 15-min ingest
case "$PLATFORM" in
    Darwin)
        USER_SHORT=$(whoami)
        PLIST="$HOME/Library/LaunchAgents/com.${USER_SHORT}.claude-archive.plist"
        echo "==> registering launchd plist: $PLIST"
        sed "s|<USERNAME>|${USER_SHORT}|g" \
            "$SKILL_DIR/scripts/launchd.plist.template" > "$PLIST"
        launchctl unload "$PLIST" 2>/dev/null || true
        launchctl load "$PLIST"
        echo "    launchd loaded"
        ;;
    Linux)
        CRON_LINE="*/15 * * * * $BIN build >/dev/null 2>&1"
        if crontab -l 2>/dev/null | grep -q "claude-archive\|crs build"; then
            echo "==> crontab already has a claude-archive entry — leaving as-is"
        else
            echo "==> adding crontab entry (every 15 min)"
            ( crontab -l 2>/dev/null; echo "$CRON_LINE" ) | crontab -
        fi
        ;;
    *)
        echo "    !! unknown platform '$PLATFORM' — schedule the 15-min ingest yourself:"
        echo "       $BIN build"
        ;;
esac

# 8. Register SessionStart hook
if command -v jq >/dev/null 2>&1; then
    [ -f "$SETTINGS" ] || { mkdir -p "$(dirname "$SETTINGS")"; echo '{}' > "$SETTINGS"; }
    HOOK_CMD="$BIN gen-recent 2>/dev/null || true"
    if jq -e '(.hooks.SessionStart // []) | flatten | map(.command? // "") | any(test("crs gen-recent|gen-recent-context"))' \
        "$SETTINGS" >/dev/null 2>&1 ; then
        echo "    SessionStart hook already registered (skip)"
    else
        echo "==> registering SessionStart hook in $SETTINGS"
        jq --arg cmd "$HOOK_CMD" \
            '.hooks.SessionStart = ((.hooks.SessionStart // []) + [{"hooks":[{"type":"command","command":$cmd,"timeout":30}]}])' \
            "$SETTINGS" > "$SETTINGS.tmp" && mv "$SETTINGS.tmp" "$SETTINGS"
    fi
else
    echo "    (jq not installed; manually add to $SETTINGS:"
    echo "       hooks.SessionStart [{\"hooks\":[{\"type\":\"command\",\"command\":\"$BIN gen-recent 2>/dev/null || true\",\"timeout\":30}]}])"
fi

# 9. First ingest
echo "==> first ingest"
"$BIN" build --no-embed

# 10. Smoke test
echo
echo "==> smoke test:"
"$BIN" --help | head -3

echo
echo "✓ Base install complete."
echo "  - 15-min ingest:  $BIN build  (launchd / cron)"
echo "  - SessionStart:   $BIN gen-recent"
echo "  - interactive:    crs csearch / crs vsearch / crs vsearch-since"
echo
echo "Optional next step (semantic search via Ollama + bge-m3):"
echo "  ./install-semantic.sh           # native Ollama (~125 MB) + ~1.2 GB model"
echo "  ./install-semantic-docker.sh    # Docker variant"
echo
echo "Then paste the snippet from SKILL.md into ~/.claude/CLAUDE.md so future"
echo "Claude sessions know to query the archive."
