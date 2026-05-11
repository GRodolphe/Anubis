#!/usr/bin/env bash
# Usage: bash tests/check_obf.sh <script.py> [anubis flags...]
# Runs the original script, obfuscates it, runs the obfuscated version,
# and asserts their stdout matches.
set -euo pipefail

SCRIPT="$1"
shift
FLAGS=("$@")

OBF="${SCRIPT%.py}-obf.py"

# Capture expected output from the original script
EXPECTED=$(uv run python "$SCRIPT")

# Obfuscate
uv run anubis "$SCRIPT" "${FLAGS[@]}"

# Capture actual output from the obfuscated script
ACTUAL=$(uv run python "$OBF")

# Cleanup
rm -f "$OBF"

if [ "$EXPECTED" = "$ACTUAL" ]; then
    echo "PASS: $SCRIPT"
else
    echo "FAIL: $SCRIPT"
    echo "--- expected ---"
    printf '%s\n' "$EXPECTED"
    echo "--- actual ---"
    printf '%s\n' "$ACTUAL"
    exit 1
fi
