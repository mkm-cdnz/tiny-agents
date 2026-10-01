#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

sudo apt-get update
sudo apt-get install -y --no-install-recommends ca-certificates cmake curl git g++ make

if [[ ! -d "$repo_root/llama.cpp/.git" ]]; then
  git clone --depth 1 https://github.com/ggml-org/llama.cpp.git "$repo_root/llama.cpp"
else
  git -C "$repo_root/llama.cpp" pull --ff-only
fi

cmake -S "$repo_root/llama.cpp" -B "$repo_root/llama.cpp/build" \
  -DCMAKE_BUILD_TYPE=Release -DGGML_NATIVE=ON -DGGML_OPENMP=ON
cmake --build "$repo_root/llama.cpp/build" --config Release -j2 --target llama-server llama-cli

mkdir -p "$repo_root/models" "$repo_root/workspace" "$repo_root/benchmarks"
python3 -m unittest discover -s "$repo_root/tests" -v
echo "Setup complete. llama-server is at llama.cpp/build/bin/llama-server"
