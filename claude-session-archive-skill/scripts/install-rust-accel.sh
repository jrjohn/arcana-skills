#!/usr/bin/env bash
#
# install-rust-accel.sh — Optional Rust acceleration for claude-session-archive.
#
# Replaces these Python scripts with a single 4.9 MB Rust binary `crs`:
#   build.py               → crs build
#   embed_parallel.py      → crs embed-missing
#   vsearch.py             → crs vsearch
#   vsearch-since.py       → crs vsearch-since
#   csearch.py             → crs csearch
#   gen-recent-context.sh  → crs gen-recent
#
# Speedups:
#   process startup           80ms  →  <5ms     >16×
#   csearch (FTS5)            20ms  →  <5ms      >4×
#   gen-recent SKIP path      10ms  →  <5ms     ~3-5×
#   build steady-state       20-100ms → <5ms    5-20×
#   gen-recent regen path    340ms → 260ms     1.3× (Ollama-bound, not much room)
#   build cold re-ingest     6.13s → 5.86s     1.05× (I/O-bound)
#
# Real value: single 4.9 MB binary vs Python venv + sqlite_vec + requests deps.
#
# Run AFTER install.sh (base) and install-semantic.sh (Ollama + vsearch).
#
# Idempotent: re-running rebuilds + re-points hooks safely.

set -e

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARCHIVE_DIR="$HOME/claude-archive"
SRC_DIR="$ARCHIVE_DIR/crs"
BIN="$SRC_DIR/target/release/crs"
USER_BIN="$HOME/bin"
SETTINGS="$HOME/.claude/settings.json"

echo "==> install-rust-accel.sh"
echo "    skill source: $SKILL_DIR"
echo "    crs source:   $SRC_DIR"
echo "    crs binary:   $BIN"

# 1. Sanity: cargo present
if ! command -v cargo >/dev/null 2>&1; then
    echo "!! cargo not found in PATH."
    echo "   Install via: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
    echo "   Then re-run this script."
    exit 1
fi
echo "    cargo: $(cargo --version)"

# 2. Copy crs source into ~/claude-archive/crs/
mkdir -p "$SRC_DIR/src"
cp "$SKILL_DIR/scripts/crs/Cargo.toml"     "$SRC_DIR/Cargo.toml"
cp "$SKILL_DIR/scripts/crs/Cargo.lock"     "$SRC_DIR/Cargo.lock" 2>/dev/null || true
cp "$SKILL_DIR/scripts/crs/src/main.rs"    "$SRC_DIR/src/main.rs"
[ -f "$SKILL_DIR/scripts/crs/.gitignore" ] && cp "$SKILL_DIR/scripts/crs/.gitignore" "$SRC_DIR/.gitignore"

# 3. Build release binary (~6s incremental, ~2-5min from clean)
echo "==> cargo build --release  (first time ~2-5 min, deps cached afterwards)"
( cd "$SRC_DIR" && cargo build --release )
echo "    built: $(du -h "$BIN" | cut -f1) at $BIN"

# 4. Symlink to ~/bin/crs for interactive use
mkdir -p "$USER_BIN"
ln -sf "$BIN" "$USER_BIN/crs"
echo "    symlink: $USER_BIN/crs → $BIN"
case ":$PATH:" in
    *":$USER_BIN:"*) : ;;
    *)
        # Auto-append to the appropriate shell rc file (matches main README install snippet).
        # macOS default zsh → ~/.zshrc ; Linux bash → ~/.bashrc ; fall back to ~/.profile.
        case "${SHELL##*/}" in
            zsh) RC="$HOME/.zshrc" ;;
            bash) RC="$HOME/.bashrc" ;;
            *) RC="$HOME/.profile" ;;
        esac
        if [ -f "$RC" ] && grep -qE '\$HOME/bin|"~/bin"' "$RC"; then
            echo "    PATH: ~/bin already referenced in $RC — no change"
        else
            printf '\n# claude-session-archive: ensure ~/bin on PATH for crs/csearch/vsearch\nexport PATH="$HOME/bin:$PATH"\n' >> "$RC"
            echo "    PATH: appended 'export PATH=\"\$HOME/bin:\$PATH\"' to $RC (open a new shell to pick up)"
        fi
        ;;
esac

# 5. Rewire launchd plist:  python3 build.py → crs build
USER_SHORT=$(whoami)
PLIST="$HOME/Library/LaunchAgents/com.${USER_SHORT}.claude-archive.plist"
if [ -f "$PLIST" ]; then
    if grep -q "build.py" "$PLIST"; then
        echo "==> Rewiring launchd plist: $PLIST"
        # Replace the ProgramArguments block atomically with sed
        python3 - "$PLIST" "$BIN" <<'PYEOF'
import sys, re, plistlib
path, bin_path = sys.argv[1], sys.argv[2]
with open(path, 'rb') as f:
    plist = plistlib.load(f)
plist['ProgramArguments'] = [bin_path, 'build']
with open(path, 'wb') as f:
    plistlib.dump(plist, f)
print("    plist updated")
PYEOF
        launchctl unload "$PLIST" 2>/dev/null || true
        launchctl load "$PLIST"
        echo "    launchd reloaded"
    else
        echo "    plist already points to crs (skip)"
    fi
fi

# 6. Rewire SessionStart hook: gen-recent-context.sh → crs gen-recent
if [ -f "$SETTINGS" ]; then
    if grep -q "gen-recent-context.sh" "$SETTINGS"; then
        echo "==> Rewiring SessionStart hook in $SETTINGS"
        python3 - "$SETTINGS" "$BIN" <<'PYEOF'
import json, sys
p, bin_path = sys.argv[1], sys.argv[2]
with open(p) as f: d = json.load(f)
new_cmd = f"{bin_path} gen-recent 2>/dev/null || true"
changed = 0
for entry in d.get("hooks", {}).get("SessionStart", []):
    for h in entry.get("hooks", []):
        if h.get("type") == "command" and "gen-recent-context.sh" in (h.get("command") or ""):
            h["command"] = new_cmd
            changed += 1
with open(p, 'w') as f: json.dump(d, f, ensure_ascii=False, indent=2)
print(f"    rewired {changed} hook command(s)")
PYEOF
    else
        echo "    SessionStart hook already on crs (or no .sh present)"
    fi
fi

# 7. Smoke test
echo
echo "==> smoke test:"
"$BIN" --help | head -3
echo
echo "==> quick build (steady-state no-op should be <50ms):"
/usr/bin/time -p "$BIN" build --no-embed --no-refresh 2>&1 | grep -E "real|touched"

echo
echo "✓ Rust acceleration installed."
echo "  - cron build:       crs build  (every 15 min via launchd)"
echo "  - SessionStart:     crs gen-recent"
echo "  - interactive:      crs csearch / crs vsearch / crs vsearch-since"
echo "  - python scripts still in $ARCHIVE_DIR (unused but kept for fallback)"
