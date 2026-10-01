# Benchmark results

## Raspberry Pi 5 baseline — 2026-10-01

Hardware and runtime:

- Raspberry Pi 5, four Cortex-A76 cores at up to 2.4 GHz
- 4 GiB RAM and 2 GiB swap
- Debian 13 (aarch64)
- `llama.cpp` commit `552f18f`, build `0.5.0-dev`
- 4096-token context, four threads, one parallel slot

Model:

- `bartowski/Qwen_Qwen3.5-2B-GGUF`
- `Qwen_Qwen3.5-2B-Q4_K_M.gguf`
- 1,396,198,496 bytes
- Text-only test; the multimodal projector was not loaded

Observed server footprint after a completed tool call:

- Resident memory: 2,431,840 KiB (58.7% of physical RAM)
- Available system memory: approximately 1.3 GiB
- Swap used after the request: approximately 129 MiB
- No active swap-out was observed in the post-request `vmstat` sample

End-to-end prompt:

> Use the system_info tool and tell me the hostname and available memory.

Result: success. The model selected the tool, used its JSON result, and returned
the correct hostname and available-memory value.

Timing from `llama-server`:

| Phase | Tokens | Rate |
|---|---:|---:|
| Initial prompt evaluation | 459 | 34.53 tokens/s |
| Initial generation/tool call | 57 | 4.87 tokens/s |
| Tool-result prompt evaluation | 125 | 31.28 tokens/s |
| Final answer generation | 129 | 4.79 tokens/s |

The complete two-request agent turn took approximately 55.8 seconds. This is a
valid feasibility result, but not evidence of broad tool-call reliability. A
larger deterministic task suite is still required.
