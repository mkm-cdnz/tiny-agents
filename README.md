# tiny-agents

Experiments with very small, tool-using language models on a Raspberry Pi 5.

The first target is a 4 GB Raspberry Pi 5 running `llama.cpp` as an
OpenAI-compatible server. The agent itself uses only Python's standard library
so that most of the Pi's memory remains available for inference.

## Run the model as a normal chatbot

This is the best place to start. It runs the downloaded Qwen3.5-2B model as-is,
without tools or agent code.

### 1. Check power first

Sustained inference makes the Pi draw more power. Resolve any low-voltage
warning before experimenting; undervoltage can cause instability or storage
corruption. After changing the power supply or cable, reboot and check:

```bash
vcgencmd get_throttled
```

The ideal result after a fresh boot is `throttled=0x0`. Historical flags remain
set until reboot, even after voltage returns to normal.

### 2. Chat in the Pi terminal

Open a terminal on the Pi and run:

```bash
cd ~/tiny-agents
./llama.cpp/build/bin/llama-cli \
  --model models/Qwen_Qwen3.5-2B-Q4_K_M.gguf \
  --ctx-size 4096 \
  --threads 4 \
  --jinja \
  --conversation
```

Wait for the model to load, type a message, and press Enter. `llama-cli` shows
timing information after each response. Press Ctrl+C to interrupt generation or
leave the program.

Example prompts:

- `Explain what a Raspberry Pi GPIO pin is in plain English.`
- `Write a Python function that groups words by their first letter.`
- `Summarise the difference between RAM and swap.`
- `Give me five ideas for small offline projects.`

The model is only about 2 billion parameters. Expect useful but imperfect
answers, occasional factual errors, and weaker multi-step reasoning than a
large hosted model.

### 3. Optional: use the built-in web interface

Start the local server on the Pi:

```bash
cd ~/tiny-agents
./scripts/serve.sh models/Qwen_Qwen3.5-2B-Q4_K_M.gguf
```

When it reports that the server is listening, open a browser **on the Pi** and
visit:

```text
http://127.0.0.1:8080
```

The server intentionally listens only on the Pi itself. To use the interface
from another computer without exposing it to the whole network, create an SSH
tunnel on that computer:

```bash
ssh -L 8080:127.0.0.1:8080 matt@192.168.1.151
```

Keep that SSH session open, then visit `http://127.0.0.1:8080` in the other
computer's browser. Stop the server with Ctrl+C in its Pi terminal.

### What performance to expect

Our initial Pi 5 test measured approximately:

- 31–35 prompt tokens per second
- 4.8 generated tokens per second
- 2.3 GiB resident memory for the model server
- roughly 56 seconds for a complete two-request tool-calling turn

A simple chat answer may therefore take tens of seconds. See
[`benchmarks/README.md`](benchmarks/README.md) for the measured setup and full
results.

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

## Install on another Pi

```bash
cd ~/tiny-agents
./scripts/setup-pi.sh
./scripts/download-model.sh URL [filename.gguf]
./scripts/serve.sh models/model.gguf
```

## Try the experimental tool-calling agent

Only move to this section after trying the model as a normal chatbot. Start the
server:

```bash
cd ~/tiny-agents
./scripts/serve.sh models/Qwen_Qwen3.5-2B-Q4_K_M.gguf
```

In a second Pi terminal:

```bash
cd ~/tiny-agents
python3 agent.py
```

This layer currently exposes only three deliberately low-risk tools:
`system_info`, `list_files`, and `read_file`. File access is confined to the
repository's `workspace/` directory. Data-analysis and action-taking tools will
be added only after the base model is evaluated.

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
