# Agent Eyes: phone → private network → local vision → text

A small, working proof of concept, not a production service or autonomous agent.
Built on 19 October 2026 to let the owner experience Tailscale directly rather
than spend more time designing an architecture. Initial phone testing was
reported by the owner as "working well"; broader testing is ongoing.

## Start here

- [Next-agent handoff and candidate next build](HANDOFF.md)
- [Testing and feedback log](TESTING.md)

## What it does

1. Browser selects/captures one photo and accepts an editable prompt.
2. A selector lists locally installed Ollama models advertising vision support.
3. A loopback-only Python service stores the submitted photo and request.
4. One background worker calls local Ollama and stores a plain text answer.
5. Browser polls and shows status, answer and saved photo in recent history.

```text
phone browser ── private Tailscale Serve ── 127.0.0.1:8766
                                              │
                                   Ollama 127.0.0.1:11434
                                              │
                           data/history.sqlite + data/photos/
```

Tailscale supplies connectivity, not inference. No cloud model, model download,
framework install, agent orchestration, public Funnel or router forwarding was
needed. This standalone demo did not change the production Life Admin PWA or
Meshdoor. A vision language model generates text; embeddings are a separate,
future retrieval capability, not a prerequisite for this loop.

## Run

Requires Python 3 with standard library and an already-running local Ollama
with a vision-capable model. Tested runtime: Python 3.14.7 on Windows.

From this directory:

```sh
python server.py
```

Open `http://127.0.0.1:8766/` locally. For private Tailscale access, first set the
actual node FQDN on the host before starting this repo copy:

```sh
# bash / Git Bash; use your own Tailscale node hostname
export AGENT_EYES_HOST='your-node.your-tailnet.ts.net'
python server.py
```

In a separate terminal, if no existing Serve route will be overwritten:

```sh
tailscale serve status
tailscale serve --bg --yes --http=8080 http://127.0.0.1:8766
```

Open `http://<your-node-FQDN>:8080/` on the phone with Tailscale connected.
Use the configured FQDN, not an unconfigured IP or short hostname. No public
Funnel is required. Remove only this route when finished:
`tailscale serve --http=8080 off`. Stop the Python process separately.

The initial demo uses HTTP inside the encrypted Tailscale tunnel and the
browser file picker, not `getUserMedia` or geolocation. It is not a browser
secure context. Trusted HTTPS and browser-policy checks are still required
before HTTPS-PWA integration or secure-context APIs. At initial setup HTTPS
Serve needed account-side enablement; do not assume it was later completed.

## Storage and limits

- Browser converts to JPEG, quality 0.88, max dimension 1600px.
- Stored image is that resized submitted copy: **not an original/EXIF archive**.
- Every photo, prompt, model, status, answer/error and duration stays locally.
- `data/history.sqlite` table `captures`; images in `data/photos/`.
- No JSONL, EXIF/GPS extraction, embeddings, schemas, deletion UI or retention job.
- Latest 30 records displayed; all stored records remain in SQLite.
- One inference worker; best-effort admission limit of 3 queued/running jobs.
  Admission is not atomic across simultaneous requests.
- Context 4096; answer cap 512 tokens; inference timeout 900s;
  Ollama keep-alive 2 minutes. `think:false`, `stream:false`.
- Default `qwen3.5:9b` if installed; selector presence is not a compatibility or
  accuracy guarantee for every model.
- Service must stay running and host awake. No autostart, durable job replay,
  offline upload queue, cancel/retry controls, rate limiting or production auth.
- On service restart unfinished jobs become errors, not automatically replayed.
- Any tailnet member with network access to the Serve port can view captures.
  Host/origin checks are not per-user authentication. Do not expose publicly.
- Image signature checking is basic, not a full image decoder/safety boundary.
- Model output is untrusted text, never executable instructions or ground truth.

## Tests and evidence

```sh
python -m unittest discover -s . -p 'test_*.py' -v
```

Storage test uses synthetic bytes to check persistence, not image recognition.
Initial live inference used the public Ultralytics `bus.jpg` image:
`https://raw.githubusercontent.com/ultralytics/ultralytics/main/ultralytics/assets/bus.jpg`.
The request "Name the main vehicle in this photograph. Reply in one short
sentence." returned **Electric Bus** from local Qwen3.5 9B in **94.16 seconds**.
This verifies the loop, not that the bus is actually electric or the model is
accurate. Local saved result/photo were read back. Browser over the Tailscale
route selected and submitted a real image. Storage, bad input, disallowed
origin and path-traversal checks passed. Phone success is user-reported.

## Snapshot versus running demo

This directory archives the implementation while initial phone testing runs
from a separate local working directory. The only server behavior difference
in this public-safe copy is replacing hardcoded private network identifiers
with `AGENT_EYES_HOST`. UI and inference/storage behavior are unchanged.
Do not run this copy on port 8766 alongside the original demo or assume its
`data/` directory contains the existing captures. Local deployment paths and
private hostname belong in the owner's private wiki, not this repository.
No captures, prompts/answers, database, credentials, device export or model
weights are included. This copy has not replaced the running service.
