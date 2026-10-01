#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 models/model.gguf" >&2
  exit 2
fi

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
model="$1"
[[ "$model" = /* ]] || model="$repo_root/$model"

exec "$repo_root/llama.cpp/build/bin/llama-server" \
  --model "$model" --host 127.0.0.1 --port 8080 \
  --ctx-size 4096 --threads 4 --parallel 1 --jinja
