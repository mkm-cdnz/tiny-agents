---
name: pi-display
description: Deliver durable alerts to a Raspberry Pi display.
version: 0.1.0
author: Matt Millar, Hermes Agent
license: MIT
platforms: [windows, linux, macos]
---
# Pi Display

Use only when Matt requests an alert or a workflow explicitly calls for one.
POST a JSON payload to the configured Pi endpoint using `scripts/send_alert.py`.
Require `HERMES_PI_URL` and `HERMES_PI_TOKEN` from the private environment. Use
stable IDs, short titles, explicit priority, display TTL, and an expiry time.
Retry transient failures twice; never send repeatedly without the same stable ID.
Do not include secrets, full email bodies, or unapproved personal data in alerts.
This skill does not authorize email, application submission, file sharing, or TV
power actions. Report the Pi acknowledgement and leave display/CEC execution to
the Pi service.

