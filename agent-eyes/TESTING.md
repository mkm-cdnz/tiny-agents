# Agent Eyes testing and feedback

## Baseline, 19 October 2026

- VERIFIED: storage unit test passed, including retained photo bytes and text.
- VERIFIED: local HTTP and Tailscale URL served page/models/photo/history.
- VERIFIED: invalid input, disallowed Origin and photo path traversal rejected.
- VERIFIED: public bus.jpg + Qwen3.5:9b yielded text `Electric Bus` in 94.16s.
  This is a transport/inference/persistence smoke test, not accuracy ground truth.
- VERIFIED: desktop browser selected an image, submitted it through Tailscale,
  and displayed the accepted/running job and an earlier completed result.
- USER-CONFIRMED: owner tested on phone and said it was "working well".
- UNKNOWN: exact phone test corpus, network type, timings, model comparisons,
  metadata fidelity, long-session behavior and sleep/reconnect resilience.

## Suggested lightweight test set — not a requirement to complete a benchmark

| Try | Look for | Why it matters |
| --- | --- | --- |
| Ordinary object + editable prompt | Useful answer; correct model/result association | Baseline usefulness |
| Small label/receipt text | Readability, invented details, crop/resize effects | OCR limits |
| Same photo/prompt across two installed models | Accepted answer vs wait time | Choose by evidence |
| Mobile data with Wi-Fi off | Page/upload/result reachability | Real field use |
| Two submissions; leave/reopen page | Clear status and persistent history | Async usability |
| Host asleep, model error or restart, when safe | Honest error; no false completed result | Recovery needs |
| Scene useful for future capture work | What advice actually improves the next capture? | Meshdoor direction |

Do not interrupt someone else's active tests or restart the host just to check
failure handling. Don't publish photos, precise locations, people or sensitive
text. Full original/EXIF preservation and geolocation are not implemented.

## Feedback record template

Store filled-in private examples in the owner's wiki, not public Git history.

- Task / intended outcome:
- Capture/job reference (local only):
- Model:
- Network (home Wi-Fi / mobile data / other):
- Wait time (measured / estimated):
- What was useful:
- What was wrong or missing:
- What the owner wanted to do next:
- Smallest justified change:
- Evidence status (observed / user-reported / proposed):

No further feedback has been inferred from the initial "working well" report.
