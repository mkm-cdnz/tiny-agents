#!/bin/sh
set -eu
run_user="${SUDO_USER:-$(id -un)}"
case "$run_user" in (*[!a-zA-Z0-9_.-]*|'') echo "invalid service user" >&2; exit 1;; esac
install -d -m 0755 /opt/hermes-pi-alerts /var/lib/hermes-pi-alerts
install -m 0755 receiver.py /opt/hermes-pi-alerts/receiver.py
sed "s/^User=.*/User=$run_user/" hermes-pi-alerts.service > /etc/systemd/system/hermes-pi-alerts.service
if [ ! -f /etc/hermes-pi-alerts.env ]; then
  token=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
  printf 'HERMES_PI_TOKEN=%s\nHERMES_PI_DISPLAY_COMMAND=\n' "$token" > /etc/hermes-pi-alerts.env
  chmod 0600 /etc/hermes-pi-alerts.env
fi
systemctl daemon-reload
systemctl enable --now hermes-pi-alerts.service
systemctl --no-pager --full status hermes-pi-alerts.service
