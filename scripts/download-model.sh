#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "usage: $0 URL [filename.gguf]" >&2
  exit 2
fi

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
url="$1"
filename="${2:-${url##*/}}"
case "$filename" in *.gguf) ;; *) echo "filename must end in .gguf" >&2; exit 2 ;; esac

mkdir -p "$repo_root/models"
curl --fail --location --continue-at - --output "$repo_root/models/$filename" "$url"
