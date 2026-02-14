#!/bin/bash
set -e

if command -v gh &>/dev/null && ! gh extension list 2>/dev/null | grep -q copilot; then
    gh extension install github/gh-copilot 2>/dev/null || true
fi

exec "$@"
