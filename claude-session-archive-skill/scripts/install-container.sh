#!/usr/bin/env bash
#
# install-container.sh — wire claude-session-archive-skill into a containerized Claude CLI.
#
# RUN INSIDE THE CONTAINER (not on host). The skill must already be present at
# /root/.claude/skills/claude-session-archive-skill/ (typically via host bind mount + rsync).
#
# What this does (idempotent — safe to re-run):
#   1. Verifies prerequisites: cargo, jq, OLLAMA_HOST, CRS_PG_URL
#   2. Builds crs binary (skip with --skip-build if already built)
#   3. Symlinks /usr/local/bin/crs → built target
#   4. Creates /root/claude-archive/ + log file
#   5. Installs hooks in /root/.claude/hooks/
#   6. Registers hooks in /root/.claude/settings.json (jq merge — preserves existing)
#   7. Installs /etc/cron.d/crs-build (skip with --skip-cron)
#   8. Runs crs doctor for sanity check
#
# What this does NOT do (intentionally):
#   - Install pgsearchd daemon (cloud deploys use direct PG over LAN, no daemon benefit)
#   - Run initial backfill (kick manually after install — see references/cloud-deployment.md §7)
#   - Write CLAUDE.md (use templates/CLAUDE.md.cloud-agent.template — owner customizes)
#
# Flags:
#   --skip-build              Don't rebuild crs (use existing target/release/crs)
#   --skip-cron               Don't install /etc/cron.d/crs-build
#   --register-hooks-only     Only do step 6 (re-merge into settings.json)
#   --user <name>             Run-as user for cron jobs (default: claude-agent)
#   -h|--help                 Show this help
#
set -euo pipefail

SKILL_DIR="/root/.claude/skills/claude-session-archive-skill"
CLAUDE_HOME="/root/.claude"
ARCHIVE_DIR="/root/claude-archive"
BIN_PATH="/usr/local/bin/crs"
RUNTIME_USER="claude-agent"
DO_BUILD=1
DO_CRON=1
HOOKS_ONLY=0

# ───────── arg parse ─────────
while [ $# -gt 0 ]; do
  case "$1" in
    --skip-build)          DO_BUILD=0; shift ;;
    --skip-cron)           DO_CRON=0; shift ;;
    --register-hooks-only) HOOKS_ONLY=1; shift ;;
    --user)                RUNTIME_USER="$2"; shift 2 ;;
    -h|--help)             sed -n '2,30p' "$0"; exit 0 ;;
    *) echo "unknown flag: $1" >&2; exit 2 ;;
  esac
done

log() { printf "[install-container] %s\n" "$*"; }
die() { printf "[install-container] FATAL: %s\n" "$*" >&2; exit 1; }

# ───────── 1. prereq check ─────────
log "Checking prerequisites..."
command -v cargo >/dev/null || die "cargo not found — install rustup first"
command -v jq    >/dev/null || die "jq not found — apt-get install -y jq"
[ -n "${OLLAMA_HOST:-}" ] || die "OLLAMA_HOST env not set (expected http://<ollama-container>:11434)"
[ -n "${CRS_PG_URL:-}${CRS_PG_HOST:-}" ] || die "CRS_PG_URL (or CRS_PG_HOST) env not set"
[ -d "$SKILL_DIR" ] || die "skill not found at $SKILL_DIR — rsync it first"

# ───────── 6. hooks-only short-circuit ─────────
register_hooks_in_settings() {
  local settings="$CLAUDE_HOME/settings.json"
  [ -f "$settings" ] || echo '{}' > "$settings"
  cp "$settings" "$settings.bak-pre-install"

  jq --arg pre "$CLAUDE_HOME/hooks/archive-preflight.sh" \
     --arg auto "$CLAUDE_HOME/hooks/auto-vsearch-on-prompt.sh" \
     --arg gen "$ARCHIVE_DIR/crs/target/release/crs gen-recent 2>/dev/null || true" '
    .hooks //= {}
    | .hooks.SessionStart = [{hooks: [{type: "command", command: $gen, timeout: 30}]}]
    | .hooks.PreToolUse = [
        {matcher: "Bash", hooks: [{type: "command", command: $pre, timeout: 5}]},
        {matcher: "Read", hooks: [{type: "command", command: $pre, timeout: 5}]}
      ]
    | .hooks.UserPromptSubmit = [{hooks: [{type: "command", command: $auto, timeout: 5}]}]
  ' "$settings" > "$settings.tmp"
  mv "$settings.tmp" "$settings"
  log "Registered hooks in $settings (backup at $settings.bak-pre-install)"
}

if [ "$HOOKS_ONLY" = "1" ]; then
  register_hooks_in_settings
  log "hooks-only mode — done"
  exit 0
fi

# ───────── 2. build crs ─────────
CRS_SRC="$SKILL_DIR/scripts/crs"
CRS_BIN="$CRS_SRC/target/release/crs"
if [ "$DO_BUILD" = "1" ]; then
  log "Building crs (cargo build --release --features pg-backend)..."
  (cd "$CRS_SRC" && cargo build --release --features pg-backend)
fi
[ -x "$CRS_BIN" ] || die "crs binary missing at $CRS_BIN — run without --skip-build"

# ───────── 3. symlink + archive dir ─────────
log "Symlinking $BIN_PATH → $CRS_BIN"
ln -sf "$CRS_BIN" "$BIN_PATH"

log "Creating $ARCHIVE_DIR"
mkdir -p "$ARCHIVE_DIR"
chown -R "$RUNTIME_USER:$RUNTIME_USER" "$ARCHIVE_DIR" 2>/dev/null || true

# Also mirror binary to /root/claude-archive/crs/target/release/ so old install paths still work
mkdir -p "$ARCHIVE_DIR/crs/target/release"
cp -f "$CRS_BIN" "$ARCHIVE_DIR/crs/target/release/crs" 2>/dev/null || \
  log "WARN: could not copy binary into $ARCHIVE_DIR/crs/... (likely Text file busy from running crs)"

# ───────── 4 & 5. hooks ─────────
log "Installing hooks to $CLAUDE_HOME/hooks/"
mkdir -p "$CLAUDE_HOME/hooks"
cp -f "$SKILL_DIR/scripts/archive-preflight.sh"      "$CLAUDE_HOME/hooks/"
cp -f "$SKILL_DIR/scripts/auto-vsearch-on-prompt.sh" "$CLAUDE_HOME/hooks/"
chmod +x "$CLAUDE_HOME/hooks/"*.sh

register_hooks_in_settings

# ───────── 7. cron ─────────
if [ "$DO_CRON" = "1" ]; then
  log "Installing /etc/cron.d/crs-build"
  if [ -f /etc/cron.d/crs-build ]; then
    log "  existing entry — backing up to /etc/cron.d/crs-build.bak"
    cp /etc/cron.d/crs-build /etc/cron.d/crs-build.bak
  fi
  # Render template with current env
  sed \
    -e "s|OLLAMA_HOST=.*|OLLAMA_HOST=${OLLAMA_HOST}|" \
    -e "s|CRS_PG_URL=.*|CRS_PG_URL=${CRS_PG_URL:-}|" \
    -e "s|claude-agent |${RUNTIME_USER} |" \
    "$SKILL_DIR/templates/crs-build.cron" > /etc/cron.d/crs-build
  chmod 0644 /etc/cron.d/crs-build
  chown root:root /etc/cron.d/crs-build
  touch "$ARCHIVE_DIR/crs-build.log"
  chown "$RUNTIME_USER:$RUNTIME_USER" "$ARCHIVE_DIR/crs-build.log"
fi

# ───────── 8. doctor ─────────
log "Running crs doctor..."
"$BIN_PATH" doctor || log "doctor reported issues — see output above"

log "Install complete. Next steps:"
log "  1. Customize $SKILL_DIR/templates/CLAUDE.md.cloud-agent.template, then cp to $CLAUDE_HOME/CLAUDE.md"
log "  2. Kick first backfill: docker exec -d -u $RUNTIME_USER <container> bash -c 'HOME=/root crs build > $ARCHIVE_DIR/crs-build.log 2>&1'"
log "  3. After ~10 min, verify with: crs vsearch '<something your agent has logged>'"
