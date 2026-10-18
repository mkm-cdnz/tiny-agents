# Agent Eyes — next-agent handoff

Recorded 19 October 2026. Read README.md and TESTING.md first.

## Intent and authority

Owner wanted a tangible, minimal phone-photo + editable-prompt → local host
vision model → saved text → phone experience, to learn what Tailscale enables.
Owner selected an installed-model chooser and retention of photo + prompt +
answer. Initial phone test is reported as working well. Owner is continuing
tests and wants lessons used to refine this into useful small tools, eventually
applying the techniques to **Meshdoor**. No immediate Meshdoor deployment,
platform rewrite, cloud GPU purchase or autonomous action is authorised.

Open source/homebrewing and a cloud/edge mix appeal to the owner; do not confuse
that preference with permission to move private photos to cloud inference.

## First action next session

Ask for the owner's testing feedback before proposing more features. Check
private wiki journal/project notes and current live health; don't rebuild a
working flow or restart a testing host without checking. Private capture data
is on the current deployment host, not in this repo. Do not upload it to GitHub.

Collect: intended task, model, network (Wi-Fi vs cellular), good/bad answer,
useful wait time, friction and what the owner actually wanted to do next.
Distinguish observed evidence from suggested features. Save specific feedback
in the private wiki; only redacted, approved general lessons belong here.

## Recommended next build — PROPOSED, feedback-gated

**A repeatable capture-and-review tool for one real task**, reusing this exact
photo/prompt/result path. Not an agent framework or vector database.

Choose the task from testing. A small set of saved prompt presets, rerunning
the same stored photo with another model, and a simple human useful/not-useful
mark would make comparison cheaper; implement only the subset that addresses
observed friction. Preserve the input provenance and measure wait time and
accepted output rather than only whether inference returned text.

Acceptance for one follow-up slice:
- Owner can perform one repeated real task with less typing/re-taking photos.
- Submitted image, exact prompt/model and answer remain attributable.
- Owner can identify a useful result versus an incorrect one.
- Existing phone loop, privacy boundaries and captured data remain intact.
- Tests cover the changed behavior; no claim that all models are benchmarked.

If testing instead exposes connection failures or unusable wait times, fix that
first: test real Wi-Fi↔mobile-data handover, image sizing/OCR trade-off or
measured inference on another authorised host. HTTPS is first only when needed
for secure-context APIs, PWA integration or an observed UX/security requirement.

## Small route toward Meshdoor — not approved implementation

1. **Feedback and one useful tool:** presets/review/model comparison only as
   justified above. This establishes what inputs/results users actually need.
2. **Capture integrity before photosets:** preserve original media and metadata
   explicitly; separate immutable originals from inference thumbnails. Current
   1600px JPEG copies are NOT suitable originals for photogrammetry pipelines.
3. **A standalone photoset preflight report, only after reuse discovery:**
   Meshdoor already documents metadata reports and immutable manifests. Inspect
   those first, then reuse or extend rather than build a duplicate scanner.
   Deterministic dimensions, EXIF, duplicates, blur/exposure checks can be combined
   with clearly labelled optional model observations and human review. Do not
   pretend a VLM can certify adequate overlap, reconstruction success or survey
   accuracy from a single photo.
4. **Meshdoor adapter only after real evidence:** inspect existing Meshdoor
   code/contracts and staging boundaries, then pass reviewed capture/report
   artifacts into its actual workflow. Do not duplicate existing intake or
   pricing tools. Quote/payment/cloud reconstruction remain separate decisions.

The owner specifically wants the techniques to reach Meshdoor eventually;
this does not supersede other projects' current scope or justify immediate
integration. No Meshdoor backend, payment, deployment or integration was
verified in this work.

## Useful implementation boundaries already present

- Capture UI: `index.html` — model selector, JPEG preprocessing, async submit,
  polling, safe text rendering and latest-history display.
- Service: `server.py` — loopback HTTP, input checks, single inference worker.
- Model adapter: `ollama()` plus `process()` — native `/api/chat`.
- Persistence: `Store` — SQLite records + submitted photo files.
- No model-selected actions, shell execution, cloud model or embeddings.

## Known rough edges to revisit only when justified

Security: trusted-tailnet only; no account-level auth or fine-grained ACL work.
Admission count is non-atomic and only scans recent 30; cannot promise a hard
queue bound under concurrency. Requests accept basic image signatures only.
All readable captures are available to allowed tailnet clients. No retention
controls; stored originals are actually resized copies. No offline queue or
restart recovery. 512 output tokens can truncate long answers; success does
not prove completeness. Polling errors are quiet; long jobs have no cancel UI.
Model capability flags do not guarantee backend supports every model's image
or thinking parameters. Live service lifecycle is manual, not a Windows service.

Do not retroactively label these as proven problems from owner testing.
They are code-review limitations of the throwaway baseline.
