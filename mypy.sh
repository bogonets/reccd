#!/usr/bin/env bash

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" || exit; pwd)

"$ROOT_DIR/python" -m mypy \
    --config-file="${ROOT_DIR}/mypy.ini" \
    "$ROOT_DIR/setup.py" \
    "$ROOT_DIR/reccd/" \
    "$ROOT_DIR/test/"
