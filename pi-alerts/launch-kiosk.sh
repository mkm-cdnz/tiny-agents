#!/bin/sh
set -eu
exec chromium --kiosk --noerrdialogs --disable-infobars --check-for-update-interval=31536000 http://127.0.0.1:8788/
