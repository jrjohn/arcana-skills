#!/usr/bin/env bash
# render-graph.sh — turn a markdown graph-spec into a standalone HTML page.
# The page renders Markdown + Mermaid (+ optional markmap mind map) client-side.
#
# Usage:
#   render-graph.sh <spec.md> <out.html> [--report] [--self-host]
#
#   --report      polished template: an interactive markmap mind map (rendered statically by
#                 the markmap autoloader, so it auto-fits) + themed Mermaid + cards. The spec's
#                 ```markmap block becomes the mind map; its leading "# H1" becomes the page
#                 title; everything else (prose + ```mermaid) becomes the body.
#   --self-host   reference ./lib/*.min.js instead of CDN (run fetch-mermaid.sh first).
#
# Deps: awk/sed only (POSIX). Portable to macOS (BSD) and Linux (GNU).
set -euo pipefail

[ $# -ge 2 ] || { echo "usage: render-graph.sh <spec.md> <out.html> [--report] [--self-host]" >&2; exit 2; }
SPEC="$1"; OUT="$2"; shift 2
REPORT=0; SELFHOST=0
for a in "$@"; do
  case "$a" in
    --report) REPORT=1;;
    --self-host) SELFHOST=1;;
    *) echo "unknown flag: $a" >&2; exit 2;;
  esac
done
HERE="$(cd "$(dirname "$0")" && pwd)"
TMPL="$HERE/../templates/$([ "$REPORT" = 1 ] && echo report.html.tmpl || echo graph.html.tmpl)"
[ -f "$SPEC" ] || { echo "spec not found: $SPEC" >&2; exit 1; }
[ -f "$TMPL" ] || { echo "template not found: $TMPL" >&2; exit 1; }

TITLE="$(grep -m1 '^# ' "$SPEC" | sed 's/^# *//' || true)"
[ -n "$TITLE" ] || TITLE="$(basename "$SPEC" .md)"

ESC="$(mktemp)"; MM="$(mktemp)"; CT="$(mktemp)"
trap 'rm -f "$ESC" "$MM" "$CT"' EXIT

if [ "$REPORT" = 1 ]; then
  # split: markmap block -> MM ; rest minus first H1 -> CT
  awk -v mmf="$MM" -v ctf="$CT" '
    /^```markmap[ \t]*$/ { inmm=1; next }
    inmm && /^```[ \t]*$/ { inmm=0; next }
    inmm { print > mmf; next }
    !h1 && /^# / { h1=1; next }
    { print > ctf }
  ' "$SPEC"
  sed 's#</script>#<\\/script>#g' "$MM" > "$MM.e" && mv "$MM.e" "$MM"
  sed 's#</script>#<\\/script>#g' "$CT" > "$CT.e" && mv "$CT.e" "$CT"
  awk -v cf="$CT" -v mf="$MM" -v title="$TITLE" '
    index($0,"{{CONTENT}}") { while ((getline l < cf) > 0) print l; next }
    index($0,"{{MINDMAP}}") { while ((getline l < mf) > 0) print l; next }
    { gsub(/\{\{TITLE\}\}/, title); print }
  ' "$TMPL" > "$OUT"
else
  sed 's#</script>#<\\/script>#g' "$SPEC" > "$ESC"
  awk -v specfile="$ESC" -v title="$TITLE" '
    index($0,"{{CONTENT}}") { while ((getline l < specfile) > 0) print l; next }
    { gsub(/\{\{TITLE\}\}/, title); print }
  ' "$TMPL" > "$OUT"
fi

if [ "$SELFHOST" = 1 ]; then
  MERMAID="./lib/mermaid.min.js"; MARKED="./lib/marked.min.js"; MARKMAP="./lib/markmap-autoloader.js"
else
  MERMAID="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"
  MARKED="https://cdn.jsdelivr.net/npm/marked@12/marked.min.js"
  MARKMAP="https://cdn.jsdelivr.net/npm/markmap-autoloader@0.18"
fi
sed -e "s#{{MERMAID_SRC}}#${MERMAID}#" -e "s#{{MARKED_SRC}}#${MARKED}#" -e "s#{{MARKMAP_SRC}}#${MARKMAP}#" "$OUT" > "$OUT.tmp" && mv "$OUT.tmp" "$OUT"

echo "rendered: $OUT  (title='$TITLE', template=$([ "$REPORT" = 1 ] && echo report || echo graph), libs=$([ "$SELFHOST" = 1 ] && echo self-host || echo cdn))"
