#!/usr/bin/env bash
#
# install-semantic.sh — Install Ollama + bge-m3 model on top of base archive.
#
# Run AFTER you've installed the base claude-session-archive (./install.sh).
# This adds the embedding stack so vsearch (semantic) works in addition to
# csearch (FTS5 lexical).
#
# What it does:
#   1. Downloads Ollama native binary (no brew, no compile, ~125 MB)
#   2. Registers Ollama with launchd (macOS) for auto-start + crash restart
#   3. Pulls bge-m3 model (~1.2 GB)
#   4. Kicks off parallel backfill in background via `crs embed-missing`
#      (~2-3 hr for 100k rows on Apple Silicon, Metal-accelerated)
#
# No Python required — embedding goes through `crs` (Rust). The crs binary
# was already built by install.sh.
#
# Idempotent: re-running skips already-completed steps.

set -e

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARCHIVE_DIR="$HOME/claude-archive"
BIN_DIR="$HOME/bin"
CRS_BIN="$ARCHIVE_DIR/crs/target/release/crs"

echo "==> install-semantic.sh"
echo "    skill source: $SKILL_DIR"
echo "    archive dir:  $ARCHIVE_DIR"

# 0. Sanity: base install done?
if [ ! -x "$CRS_BIN" ]; then
    echo "!! crs binary not found at $CRS_BIN"
    echo "   Run ./install.sh first (base setup)."
    exit 1
fi
echo "    crs:    $CRS_BIN"

mkdir -p "$ARCHIVE_DIR" "$BIN_DIR"

# 1. Ollama binary (macOS native)
if ! command -v ollama >/dev/null 2>&1; then
    echo "==> downloading ollama binary..."
    OLLAMA_VER="v0.21.2"
    curl -fL "https://github.com/ollama/ollama/releases/download/${OLLAMA_VER}/ollama-darwin.tgz" \
        -o /tmp/ollama-darwin.tgz
    mkdir -p "$ARCHIVE_DIR/ollama-bin"
    tar -xzf /tmp/ollama-darwin.tgz -C "$ARCHIVE_DIR/ollama-bin"
    chmod +x "$ARCHIVE_DIR/ollama-bin/ollama"
    ln -sf "$ARCHIVE_DIR/ollama-bin/ollama" "$BIN_DIR/ollama"
    rm /tmp/ollama-darwin.tgz
fi
echo "    ollama: $(ollama --version 2>/dev/null || echo 'pending start')"

# 2. Register Ollama with launchd (auto-start at login + restart on crash)
USER_SHORT=$(whoami)
PLIST="$HOME/Library/LaunchAgents/com.${USER_SHORT}.ollama.plist"
if [ ! -f "$PLIST" ]; then
    echo "==> registering ollama with launchd..."
    sed "s|<USERNAME>|${USER_SHORT}|g" "$SKILL_DIR/scripts/ollama.plist.template" > "$PLIST"
    launchctl unload "$PLIST" 2>/dev/null || true
    launchctl load "$PLIST"
    sleep 3
fi
# Fallback if user didn't want launchd
if ! curl -s --max-time 2 http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "==> starting ollama serve (no launchd) ..."
    nohup ollama serve > "$ARCHIVE_DIR/ollama.log" 2>&1 &
    sleep 3
fi
curl -s --max-time 2 http://localhost:11434/api/tags >/dev/null && echo "    ollama daemon: up"

# 3. Pull embedding model
if ! ollama list 2>/dev/null | grep -q bge-m3; then
    echo "==> pulling bge-m3 (~1.2 GB)..."
    ollama pull bge-m3
fi
echo "    model ready:"
ollama list | grep bge-m3 || true

# 4. Kick off backfill via crs embed-missing
TOTAL_ROWS=$(sqlite3 "$ARCHIVE_DIR/sessions.db" "SELECT COUNT(*) FROM msg" 2>/dev/null || echo 0)
EMBED_ROWS=$(sqlite3 "$ARCHIVE_DIR/sessions.db" "SELECT COUNT(*) FROM msg_vec" 2>/dev/null || echo 0)
PENDING=$((TOTAL_ROWS - EMBED_ROWS))

echo "==> rows to backfill: $PENDING (of $TOTAL_ROWS total)"
if [ "$PENDING" -gt 0 ]; then
    echo "==> launching parallel backfill in background (8 workers)"
    echo "    log: $ARCHIVE_DIR/backfill.log"
    echo "    estimate: ~$((PENDING / 420)) min on Apple Silicon (bge-m3 ~7 emb/sec @ 8 workers)"
    nohup "$CRS_BIN" embed-missing --workers 8 \
        > "$ARCHIVE_DIR/backfill.log" 2>&1 &
    echo "    PID: $!"
    echo
    echo "    Track progress:"
    echo "      tail -f $ARCHIVE_DIR/backfill.log"
    echo "      sqlite3 $ARCHIVE_DIR/sessions.db 'SELECT COUNT(*) FROM msg_vec'"
fi

echo
echo "==> done. Once backfill finishes:"
echo "      crs vsearch '上次廣播 deny log 怎麼解的'"
echo "      crs vsearch 'how to fix wifi disconnect' network"
