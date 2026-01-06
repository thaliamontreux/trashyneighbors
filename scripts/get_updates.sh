#!/bin/bash
set -euo pipefail

: "${GITHUB_TOKEN:?Set GITHUB_TOKEN in the environment first}"

REPO="https://github.com/thaliamontreux/trashyneighbors.git"
DEST="${1:-$HOME/trashyneighbors}"

# This makes git use the token for github.com without writing it into the repo config
git -c "http.extraheader=Authorization: Bearer ${GITHUB_TOKEN}" clone "$REPO" "$DEST" 2>/dev/null \
  || git -c "http.extraheader=Authorization: Bearer ${GITHUB_TOKEN}" -C "$DEST" pull --ff-only
