#!/usr/bin/env bash
# fetch-mermaid.sh — pin mermaid.min.js + marked.min.js into a local lib/ dir so
# rendered graphs work fully offline / air-gapped (e.g. an internal dashboard with
# no outbound internet). Only needed for `render-graph.sh --self-host`.
#
# Usage: fetch-mermaid.sh [target-lib-dir]   (default: ./lib next to this script's parent)
set -euo pipefail
DEST="${1:-$(cd "$(dirname "$0")/.." && pwd)/examples/lib}"
mkdir -p "$DEST"
MERMAID_URL="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"
MARKED_URL="https://cdn.jsdelivr.net/npm/marked@12/marked.min.js"
MARKMAP_URL="https://cdn.jsdelivr.net/npm/markmap-autoloader@0.18/dist/index.js"
echo "→ $DEST"
curl -fsSL "$MERMAID_URL" -o "$DEST/mermaid.min.js"
curl -fsSL "$MARKED_URL"  -o "$DEST/marked.min.js"
curl -fsSL "$MARKMAP_URL" -o "$DEST/markmap-autoloader.js"   # for --report mind maps
echo "fetched: mermaid.min.js + marked.min.js + markmap-autoloader.js into $DEST"
echo "note: these are .gitignore'd — they are CDN mirrors, not source. Re-fetch on each clone."
