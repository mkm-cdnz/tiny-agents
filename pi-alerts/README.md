# Hermes Pi Alerts

An authenticated, durable alert receiver for a Raspberry Pi. It accepts JSON
alerts, stores them in SQLite, and hands them to a display adapter. It does not
send mail or expose the TV-control policy by default.

## Run

```bash
export HERMES_PI_TOKEN='use-a-long-random-token'
python3 receiver.py --host 0.0.0.0 --port 8787 --db alerts.db
```

`POST /v1/alerts` returns `202` only after the alert is durably queued. Repeat
delivery of the same `id` is idempotent. `GET /health` is unauthenticated and
`GET /v1/alerts/<id>` requires the token.

The display and CEC adapters are intentionally interfaces for now. Wire them to
the existing Pi display program after its input contract and TV model are known.

