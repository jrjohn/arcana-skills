#!/usr/bin/env bash
#
# install-semantic.sh — Install Ollama + sqlite-vec + vsearch on top of base archive.
#
# Run AFTER you've installed the base claude-session-archive-skill (Steps 1-6).
# This adds optional Step 7: semantic search via local embeddings.
#
# Usage:
#   ./install-semantic.sh
#
# What it does:
#   1. Downloads Ollama binary (no brew, no compile, ~125MB)
#   2. Starts Ollama daemon
#   3. Pulls nomic-embed-text model (~274MB)
#   4. Creates ~/claude-archive/.venv with sqlite-vec + requests
#   5. Copies embed.py / vsearch.py to ~/claude-archive/
#   6. Copies vsearch wrapper to ~/bin/
#   7. Kicks off backfill in background (~30-90 min for 100k rows)
#
# Idempotent: re-running skips already-completed steps.

set -e

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARCHIVE_DIR="$HOME/claude-archive"
BIN_DIR="$HOME/bin"

echo "==> install-semantic.sh"
echo "    skill source: $SKILL_DIR"
echo "    archive dir:  $ARCHIVE_DIR"

mkdir -p "$ARCHIVE_DIR" "$BIN_DIR"

# 1. Ollama binary
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
if ! ollama list 2>/dev/null | grep -q nomic-embed-text; then
    echo "==> pulling nomic-embed-text (~274 MB)..."
    ollama pull nomic-embed-text
fi
echo "    model ready:"
ollama list | grep nomic-embed-text || true

# 4. Python venv
if [ ! -d "$ARCHIVE_DIR/.venv" ]; then
    echo "==> creating venv at $ARCHIVE_DIR/.venv"
    python3 -m venv "$ARCHIVE_DIR/.venv"
fi
echo "==> installing python deps..."
"$ARCHIVE_DIR/.venv/bin/pip" install --quiet --upgrade pip
"$ARCHIVE_DIR/.venv/bin/pip" install --quiet sqlite-vec requests
echo "    sqlite-vec: $($ARCHIVE_DIR/.venv/bin/python -c 'import sqlite_vec; print(sqlite_vec.__version__)')"

# 5. Copy scripts
echo "==> installing embed.py + vsearch.py..."
cp "$SKILL_DIR/scripts/embed.py"    "$ARCHIVE_DIR/embed.py"
cp "$SKILL_DIR/scripts/vsearch.py"  "$ARCHIVE_DIR/vsearch.py"
chmod +x "$ARCHIVE_DIR/embed.py" "$ARCHIVE_DIR/vsearch.py"

# 6. vsearch wrapper
echo "==> installing vsearch CLI..."
cp "$SKILL_DIR/scripts/vsearch" "$BIN_DIR/vsearch"
chmod +x "$BIN_DIR/vsearch"

# 7. Sync newer build.py (with maybe_embed_new)
echo "==> updating build.py (adds maybe_embed_new hook)..."
cp "$SKILL_DIR/scripts/build.py" "$ARCHIVE_DIR/build.py"
chmod +x "$ARCHIVE_DIR/build.py"

# 8. Kick off backfill
TOTAL_ROWS=$(sqlite3 "$ARCHIVE_DIR/sessions.db" "SELECT COUNT(*) FROM msg" 2>/dev/null || echo 0)
EMBED_ROWS=$(sqlite3 "$ARCHIVE_DIR/sessions.db" "SELECT COUNT(*) FROM msg_vec" 2>/dev/null || echo 0)
PENDING=$((TOTAL_ROWS - EMBED_ROWS))

echo "==> rows to backfill: $PENDING (of $TOTAL_ROWS total)"

if [ "$PENDING" -gt 0 ]; then
    echo "==> launching backfill in background"
    echo "    log: $ARCHIVE_DIR/backfill.log"
    echo "    estimate: ~$((PENDING / 1800)) min on Apple Silicon"
    nohup "$ARCHIVE_DIR/.venv/bin/python" "$ARCHIVE_DIR/embed.py" \
        > "$ARCHIVE_DIR/backfill.log" 2>&1 &
    echo "    PID: $!"
    echo
    echo "    Track progress:"
    echo "      tail -f $ARCHIVE_DIR/backfill.log"
    echo "      sqlite3 $ARCHIVE_DIR/sessions.db 'SELECT COUNT(*) FROM msg_vec'"
fi

echo
echo "==> done. Once backfill finishes:"
echo "      vsearch '上次廣播 deny log 怎麼解的'"
echo "      vsearch 'how to fix wifi disconnect' network"
