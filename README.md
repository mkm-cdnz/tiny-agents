# tiny-agents

Experiments with very small, tool-using language models on a Raspberry Pi 5.

The first target is a 4 GB Raspberry Pi 5 running `llama.cpp` as an
OpenAI-compatible server. The agent itself uses only Python's standard library
so that most of the Pi's memory remains available for inference.

## Architecture

```text
terminal -> agent.py -> llama-server (/v1/chat/completions)
                         |
                         +-> model-selected tool calls
                               |- system_info
                               |- list_files
                               `- read_file
```

All file tools are restricted to `./workspace`. The agent never executes shell
commands supplied by the model.

## Pi setup

```bash
cd ~/tiny-agents
./scripts/setup-pi.sh
./scripts/download-model.sh URL [filename.gguf]
./scripts/serve.sh models/model.gguf
```

In another terminal, run `python3 agent.py`.

| Variable | Default | Purpose |
|---|---|---|
| `TINY_AGENTS_URL` | `http://127.0.0.1:8080/v1` | OpenAI-compatible API root |
| `TINY_AGENTS_MODEL` | `local-model` | Model name sent to the server |
| `TINY_AGENTS_MAX_STEPS` | `8` | Maximum tool iterations per request |
| `TINY_AGENTS_WORKSPACE` | `./workspace` | File-tool sandbox |

Run tests with `python3 -m unittest discover -s tests -v`.

## Initial experiment protocol

Do not assume a model fits because its GGUF file fits in RAM. For every model,
record idle available memory, server resident memory at 4K context, prompt
processing speed, generation speed, tool-call validity, and task success. Keep
swap use at zero during normal inference.

The initial candidate is Qwen3.5-2B at Q4_K_M. It is a candidate to measure,
not a guaranteed fit: multimodal projection and image tokens add memory beyond
the text-only path.
