#!/bin/sh
set -eu
BASE="${1:-http://127.0.0.1:8765}"

check() {
  url="$1"
  code=$(wget -q -S -O /dev/null "$url" 2>&1 | awk '/HTTP\// {print $2; exit}')
  if [ "$code" != "200" ]; then
    echo "FAIL $url (HTTP $code)"
    exit 1
  fi
  echo "OK   $url"
}

check "$BASE/"
check "$BASE/index.html"
check "$BASE/cards/back.png"
check "$BASE/audio/tracks/liecio-mystical-place-relax-ambient-258070.mp3"

echo "All smoke checks passed."
