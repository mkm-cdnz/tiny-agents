#!/bin/sh
set -eu
install -d -m 0755 /opt/hermes-pi-alerts /var/lib/hermes-pi-alerts
install -m 0755 receiver.py /opt/hermes-pi-alerts/receiver.py
install -m 0644 hermes-pi-alerts.service /etc/systemd/system/hermes-pi-alerts.service
if [ ! -f /etc/hermes-pi-alerts.env ]; then
  token=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
  printf 'HERMES_PI_TOKEN=%s\nHERMES_PI_DISPLAY_COMMAND=\n' "$token" > /etc/hermes-pi-alerts.env
  chmod 0600 /etc/hermes-pi-alerts.env
fi
systemctl daemon-reload
systemctl enable --now hermes-pi-alerts.service
systemctl --no-pager --full status hermes-pi-alerts.service

