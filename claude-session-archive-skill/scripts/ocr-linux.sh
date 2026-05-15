#!/usr/bin/env bash
# Linux OCR helper for claude-session-archive v1.15+
# Requires: tesseract-ocr + tesseract-ocr-chi-tra (Debian/Ubuntu)
#           tesseract + tesseract-langpack-chi_tra (Fedora)
# Usage: ocr-linux.sh <image_path>   → text on stdout
set -euo pipefail
if [ $# -ne 1 ]; then
    echo "usage: ocr-linux.sh <image_path>" >&2
    exit 1
fi
exec tesseract "$1" stdout -l chi_tra+eng 2>/dev/null
