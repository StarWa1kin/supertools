#!/bin/sh
# Start the sibling parser privately; this script does not issue parsing requests.
set -eu

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
parser_dir=${MEDIA_PARSER_PROJECT_DIR:-"$repo_dir/../media-parser"}
python_bin=${MEDIA_PARSER_PYTHON:-"$parser_dir/.venv/bin/python"}
port=${MEDIA_PARSER_PORT:-8051}

if [ ! -f "$parser_dir/app.py" ] || [ ! -x "$python_bin" ]; then
  printf '%s\n' '请设置 MEDIA_PARSER_PROJECT_DIR 和 MEDIA_PARSER_PYTHON，指向解析项目及其 Python 环境。' >&2
  exit 1
fi

cd "$parser_dir"
# API_ONLY skips API-key authentication. Bind to loopback, never a public interface.
exec env API_ONLY=true WEB_PORT="$port" "$python_bin" -m flask \
  --app app:app run --host=127.0.0.1 --port="$port"
