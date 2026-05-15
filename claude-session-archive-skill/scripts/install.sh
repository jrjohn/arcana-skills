#!/usr/bin/env bash
#
# install.sh — Base installer for claude-session-archive (macOS / Linux).
#
# Builds the Rust binary `crs` (single ~5 MB self-contained binary, bundles
# SQLite + FTS5 + sqlite-vec) and wires up the 15-min ingest schedule.
#
# Default backend is local SQLite + sqlite-vec (single-machine, sub-ms).
# Pass --with-pg (or set WITH_PG=1) to build the optional `pg-backend` feature
# instead — routes csearch / vsearch / vsearch-since / build / embed-missing
# through a remote PostgreSQL + pgvector instance. See references/pg-backend.md.
#
# Steps:
#   1. Verify cargo is present (rustup needed)
#   2. mkdirs ~/claude-archive ~/bin
#   3. Copy crs source → cargo build --release [--features pg-backend]
#   4. ~/bin/crs symlink + PATH on shell rc (zsh / bash / sh)
#   5. ~/.sqliterc tuning
#   6. Install gen-recent-context.sh
#   7. Schedule 15-min ingest:
#        macOS  → launchd plist
#        Linux  → crontab entry
#   7b. (--with-pg only) install + load pgsearchd launchd plist on macOS
#   8.  Register SessionStart hook in ~/.claude/settings.json (needs jq)
#   8b. Install + register PreToolUse archive-preflight hook (Bash + Read)
#   8c. Install + register UserPromptSubmit auto-vsearch-on-prompt hook
#   9.  First ingest run (skipped under --with-pg if CRS_PG_PASSWORD not set)
#  10. Smoke test
#
# Idempotent: re-running rebuilds + re-points hooks safely.
#
# AFTER this: optionally run install-semantic.sh to add Ollama + bge-m3 for
# semantic vsearch. Pure FTS5 csearch works without it.

set -e

# Parse flags
WITH_PG="${WITH_PG:-0}"
for arg in "$@"; do
    case "$arg" in
        --with-pg) WITH_PG=1 ;;
        --help|-h)
            sed -n '2,32p' "$0" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
    esac
done

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
if [ "$WITH_PG" = "1" ]; then
    echo "    backend:      pg-backend (remote PostgreSQL+pgvector)"
else
    echo "    backend:      sqlite (default, local)"
fi

# 1. Sanity: cargo present
if ! command -v cargo >/dev/null 2>&1; then
    echo "!! cargo not found in PATH."
    echo "   Install Rust toolchain first:"
    echo "     curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
    echo "   Then re-run this script."
    exit 1
fi
echo "    cargo: $(cargo --version)"

# 1.5. Optional but recommended dependencies — warn early so users can decide
#      to abort + install rather than discover the gap mid-run.
echo
echo "==> Optional dependencies (none are strictly required, but recommended)"
for dep in jq sqlite3; do
    if command -v "$dep" >/dev/null 2>&1; then
        echo "    ✓ $dep: present"
    else
        case "$dep" in
            jq)
                echo "    ⚠ jq: missing"
                echo "         needed for automatic SessionStart hook registration in"
                echo "         ~/.claude/settings.json (otherwise printed for manual paste)."
                case "$PLATFORM" in
                    Darwin) echo "         install: brew install jq" ;;
                    Linux)  echo "         install: apt install jq  (or yum / pacman / apk equivalent)" ;;
                esac
                ;;
            sqlite3)
                echo "    ⚠ sqlite3 CLI: missing"
                echo "         needed only for raw SQL queries against sessions.db. The crs"
                echo "         binary already bundles SQLite, so csearch / vsearch work fine"
                echo "         without this — install only if you want \`sqlite3 ~/claude-archive/sessions.db\`."
                case "$PLATFORM" in
                    Darwin) echo "         install: brew install sqlite" ;;
                    Linux)  echo "         install: apt install sqlite3  (or yum / pacman / apk equivalent)" ;;
                esac
                ;;
        esac
    fi
done

# 2. mkdirs
mkdir -p "$ARCHIVE_DIR" "$USER_BIN"

# 3. Copy crs source into ~/claude-archive/crs/ + build
mkdir -p "$SRC_DIR/src"
cp "$SKILL_DIR/scripts/crs/Cargo.toml"  "$SRC_DIR/Cargo.toml"
cp "$SKILL_DIR/scripts/crs/Cargo.lock"  "$SRC_DIR/Cargo.lock" 2>/dev/null || true
cp "$SKILL_DIR/scripts/crs/src/main.rs" "$SRC_DIR/src/main.rs"
[ -f "$SKILL_DIR/scripts/crs/.gitignore" ] && cp "$SKILL_DIR/scripts/crs/.gitignore" "$SRC_DIR/.gitignore"

if [ "$WITH_PG" = "1" ]; then
    BUILD_FLAGS="--release --features pg-backend"
    echo "==> cargo build $BUILD_FLAGS  (first time ~3-7 min, includes postgres deps)"
else
    BUILD_FLAGS="--release"
    echo "==> cargo build --release  (first time ~2-5 min, deps cached afterwards)"
fi
# shellcheck disable=SC2086
( cd "$SRC_DIR" && cargo build $BUILD_FLAGS )
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

# 4b. (v1.15+) OCR helpers — make screenshot text searchable in csearch/vsearch.
#     OCR engine is OS-native + free:
#       macOS  → Swift CLI wrapping VNRecognizeTextRequest (Apple Vision)
#       Linux  → tesseract chi_tra+eng (system package required)
#     A 4 KB-truncated image JSON in msg.content is replaced by a short
#     [IMG:<sha256>] sentinel; `crs build` and `crs ocr-missing` walk those,
#     OCR the original bytes from the JSONL, write rows into image_ocr
#     (per-message) + image_ocr_cache (cross-machine SHA256-dedup).
mkdir -p "$ARCHIVE_DIR/bin" "$ARCHIVE_DIR/images"
case "$PLATFORM" in
    Darwin)
        if command -v swiftc >/dev/null 2>&1; then
            echo "==> building macOS OCR helper (Swift + Vision)"
            ( cd "$SKILL_DIR/scripts/ocr-mac" && swiftc -O main.swift -o "$ARCHIVE_DIR/bin/ocr-mac" )
            echo "    built: $ARCHIVE_DIR/bin/ocr-mac"
        else
            echo "    !! swiftc missing — install Xcode Command Line Tools (xcode-select --install)"
            echo "       skipping OCR helper build; screenshot text won't be searchable"
        fi
        ;;
    Linux)
        cp "$SKILL_DIR/scripts/ocr-linux.sh" "$ARCHIVE_DIR/bin/ocr-linux.sh"
        chmod +x "$ARCHIVE_DIR/bin/ocr-linux.sh"
        if command -v tesseract >/dev/null 2>&1; then
            if tesseract --list-langs 2>&1 | grep -qE '\bchi_tra\b|\bchi_sim\b'; then
                echo "    OCR: tesseract present + Chinese pack installed"
            else
                echo "    !! tesseract present but no Chinese language pack — install:"
                echo "         apt:    apt install tesseract-ocr-chi-tra"
                echo "         fedora: dnf install tesseract-langpack-chi_tra"
            fi
        else
            echo "    !! tesseract not installed — screenshots won't be searchable until you install:"
            echo "         apt:    apt install tesseract-ocr tesseract-ocr-chi-tra"
            echo "         fedora: dnf install tesseract tesseract-langpack-chi_tra"
        fi
        ;;
esac

# 4c. (--with-pg only) Apply image_ocr schema migration to bluesea PG.
#     Idempotent — safe to re-run on existing installs.
if [ "$WITH_PG" = "1" ]; then
    if command -v psql >/dev/null 2>&1; then
        : "${CRS_PG_HOST:=localhost}"
        : "${CRS_PG_PORT:=5432}"
        : "${CRS_PG_USER:=archive}"
        : "${CRS_PG_DB:=archive_main}"
        if [ -n "${CRS_PG_PASSWORD:-}" ]; then
            echo "==> applying image_ocr schema to PG (idempotent)"
            PGPASSWORD="$CRS_PG_PASSWORD" psql -h "$CRS_PG_HOST" -p "$CRS_PG_PORT" \
                -U "$CRS_PG_USER" -d "$CRS_PG_DB" \
                -v ON_ERROR_STOP=1 \
                -f "$SKILL_DIR/sql/image_ocr.sql" >/dev/null
            echo "    image_ocr_cache + image_ocr tables ready on $CRS_PG_HOST/$CRS_PG_DB"
        else
            echo "    !! CRS_PG_PASSWORD not set — apply schema manually after first build:"
            echo "         psql -h \$CRS_PG_HOST -U \$CRS_PG_USER -d \$CRS_PG_DB \\"
            echo "              -f $SKILL_DIR/sql/image_ocr.sql"
        fi
    else
        echo "    !! psql not on PATH — schema migration must be applied manually:"
        echo "       brew install libpq  # macOS"
        echo "       apt install postgresql-client  # Linux"
        echo "    then: psql ... -f $SKILL_DIR/sql/image_ocr.sql"
    fi
fi

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

# 7b. (--with-pg only) install pgsearchd daemon launchd plist on macOS.
#     The daemon holds an r2d2 connection pool over a unix socket so each
#     csearch/vsearch skips the ~700ms TLS handshake. Without it, every
#     query reconnects fresh.
if [ "$WITH_PG" = "1" ] && [ "$PLATFORM" = "Darwin" ]; then
    USER_SHORT=$(whoami)
    PGD_PLIST="$HOME/Library/LaunchAgents/com.${USER_SHORT}.pgsearchd.plist"
    PGD_TEMPLATE="$SKILL_DIR/scripts/pgsearchd.plist.template"
    if [ -f "$PGD_PLIST" ]; then
        echo "==> pgsearchd plist already present: $PGD_PLIST"
        echo "    (leaving as-is so your CRS_PG_PASSWORD env value is preserved.)"
        echo "    To regenerate from template: rm \"$PGD_PLIST\" then re-run."
    else
        echo "==> writing pgsearchd plist template: $PGD_PLIST"
        sed "s|<USERNAME>|${USER_SHORT}|g" "$PGD_TEMPLATE" > "$PGD_PLIST"
        chmod 600 "$PGD_PLIST"
        echo "    !! Edit $PGD_PLIST and replace these placeholders:"
        echo "         CRS_PG_HOST       (default: arcana.example.com)"
        echo "         CRS_PG_PASSWORD   (REPLACE_WITH_YOUR_PG_PASSWORD)"
        echo "       Then load:"
        echo "         launchctl load \"$PGD_PLIST\""
    fi
elif [ "$WITH_PG" = "1" ] && [ "$PLATFORM" = "Linux" ]; then
    echo "==> Linux pgsearchd: write a systemd user unit or an &-backgrounded launcher."
    echo "    The crs binary's pgsearchd subcommand listens on a unix socket at"
    echo "    \$XDG_CACHE_HOME/pgsearchd/pgsearchd.sock (defaults to ~/.cache/...)."
    echo "    Set CRS_PG_PASSWORD (and friends) in the unit file's Environment="
fi

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

# 8b. Install + register archive-preflight PreToolUse hook
#     - Hard-denies raw sqlite3 SEARCH (LIKE/MATCH/msg_fts/GLOB) on archive DB
#       regardless of sentinel state — csearch is the only content-search interface (v1.11+).
#     - Sentinel-gates (until vsearch/csearch runs): sqlite3 metadata, memory file grep/Read,
#       SSH/local log dig, git log --grep.
#     - Sentinel: /tmp/claude-archive-preflight-<session_id>, TTL 30 min (v1.11+).
HOOKS_DIR="$HOME/.claude/hooks"
PREFLIGHT="$HOOKS_DIR/archive-preflight.sh"
mkdir -p "$HOOKS_DIR"
echo "==> installing archive-preflight hook → $PREFLIGHT"
cp "$SKILL_DIR/scripts/archive-preflight.sh" "$PREFLIGHT"
chmod +x "$PREFLIGHT"

if command -v jq >/dev/null 2>&1; then
    PREFLIGHT_CMD="$PREFLIGHT"
    # Register PreToolUse hook for both Bash AND Read matchers (idempotent)
    for matcher in Bash Read; do
        if jq -e --arg m "$matcher" --arg c "$PREFLIGHT_CMD" \
            '(.hooks.PreToolUse // []) | map(select(.matcher == $m)) | map(.hooks // []) | flatten | map(.command? // "") | any(. == $c)' \
            "$SETTINGS" >/dev/null 2>&1 ; then
            echo "    PreToolUse $matcher hook already registered (skip)"
        else
            echo "==> registering PreToolUse $matcher hook"
            jq --arg m "$matcher" --arg c "$PREFLIGHT_CMD" \
                '.hooks.PreToolUse = ((.hooks.PreToolUse // []) + [{"matcher":$m,"hooks":[{"type":"command","command":$c,"timeout":5}]}])' \
                "$SETTINGS" > "$SETTINGS.tmp" && mv "$SETTINGS.tmp" "$SETTINGS"
        fi
    done
else
    echo "    (jq not installed; manually add to $SETTINGS PreToolUse for Bash + Read:"
    echo "       {\"matcher\":\"Bash\",\"hooks\":[{\"type\":\"command\",\"command\":\"$PREFLIGHT\",\"timeout\":5}]}"
    echo "       {\"matcher\":\"Read\",\"hooks\":[{\"type\":\"command\",\"command\":\"$PREFLIGHT\",\"timeout\":5}]})"
fi

# 8c. Install + register UserPromptSubmit auto-vsearch-on-prompt hook
#     - Detects identity / history / status / question keywords in the prompt.
#     - Runs `crs vsearch <prompt>` cross-project, injects top hits as
#       additionalContext, and pre-sets the preflight sentinel.
#     - Companion to 8b (proactive vs reactive enforcement).
#
#     Note: don't clobber a customized auto-vsearch-on-prompt.sh (e.g. one
#     that bundles an extra trigger like emotional/persona switching).
#     Detect and skip if the existing file differs from the skill version.
AUTO_VSEARCH="$HOOKS_DIR/auto-vsearch-on-prompt.sh"
SRC="$SKILL_DIR/scripts/auto-vsearch-on-prompt.sh"
if [ -f "$AUTO_VSEARCH" ]; then
    if cmp -s "$SRC" "$AUTO_VSEARCH"; then
        echo "    auto-vsearch-on-prompt hook unchanged: $AUTO_VSEARCH"
    else
        echo "    !! $AUTO_VSEARCH exists and differs from skill version — leaving as-is"
        echo "       (your version may have local customizations like a luminous-skill"
        echo "       trigger; diff manually if needed)"
    fi
else
    echo "==> installing auto-vsearch-on-prompt hook → $AUTO_VSEARCH"
    cp "$SRC" "$AUTO_VSEARCH"
    chmod +x "$AUTO_VSEARCH"
fi

if command -v jq >/dev/null 2>&1; then
    UPS_CMD="$AUTO_VSEARCH"
    if jq -e --arg c "$UPS_CMD" \
        '(.hooks.UserPromptSubmit // []) | flatten | map(.command? // "") | any(. == $c or test("auto-vsearch-on-prompt"))' \
        "$SETTINGS" >/dev/null 2>&1 ; then
        echo "    UserPromptSubmit auto-vsearch hook already registered (skip)"
    else
        echo "==> registering UserPromptSubmit auto-vsearch hook"
        jq --arg c "$UPS_CMD" \
            '.hooks.UserPromptSubmit = ((.hooks.UserPromptSubmit // []) +
                [{"hooks":[{"type":"command","command":$c,"timeout":5}]}])' \
            "$SETTINGS" > "$SETTINGS.tmp" && mv "$SETTINGS.tmp" "$SETTINGS"
    fi
else
    echo "    (jq not installed; manually add to $SETTINGS UserPromptSubmit:"
    echo "       {\"hooks\":[{\"type\":\"command\",\"command\":\"$AUTO_VSEARCH\",\"timeout\":5}]})"
fi

# 9. First ingest
if [ "$WITH_PG" = "1" ] && [ -z "${CRS_PG_PASSWORD:-}" ]; then
    echo "==> skipping first ingest (--with-pg + CRS_PG_PASSWORD not set)"
    echo "    Set CRS_PG_PASSWORD in your shell + the launchd plist, then run:"
    echo "      $BIN build"
else
    echo "==> first ingest"
    "$BIN" build --no-embed
fi

# 10. Smoke test
echo
echo "==> smoke test:"
"$BIN" --help | head -3

echo
echo "✓ Base install complete."
echo "  - 15-min ingest:        $BIN build  (launchd / cron)"
echo "  - SessionStart hook:    $BIN gen-recent"
echo "  - PreToolUse hook:      $PREFLIGHT (Bash + Read; vsearch/csearch preflight)"
echo "  - UserPromptSubmit:     $AUTO_VSEARCH (auto-vsearch on identity/history/status prompts)"
echo "  - interactive:          crs csearch / crs vsearch / crs vsearch-since"
if [ "$WITH_PG" = "1" ]; then
    echo
    echo "PG backend (--with-pg) extras:"
    echo "  - pgsearch subcommand: crs pgsearch [--vec|--fts|--hybrid] '<query>'"
    if [ "$PLATFORM" = "Darwin" ]; then
        echo "  - pgsearchd daemon:    com.$(whoami).pgsearchd  (load + check launchctl list)"
    fi
    echo "  - required env vars:   CRS_PG_PASSWORD (and CRS_PG_HOST/PORT/USER/DB if non-default)"
    echo "                         OR CRS_PG_URL='host=... port=... user=... password=... dbname=... sslmode=require'"
    echo "  - server schema + setup: see references/pg-backend.md"
fi
echo
echo "Optional next step (semantic search via Ollama + bge-m3):"
echo "  ./install-semantic.sh           # native Ollama (~125 MB) + ~1.2 GB model"
echo "  ./install-semantic-docker.sh    # Docker variant"
echo
echo "Then paste the snippet from SKILL.md into ~/.claude/CLAUDE.md so future"
echo "Claude sessions know to query the archive."
