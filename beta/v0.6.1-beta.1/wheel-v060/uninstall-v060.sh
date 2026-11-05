#!/usr/bin/env bash
set -euo pipefail
[[ $(id -u) == 0 ]] || { echo 'Usa sudo bash uninstall-v060.sh' >&2; exit 1; }
systemctl disable --now blueandme-wheel-v060.service || true
rm -f /etc/systemd/system/blueandme-wheel-v060.service
systemctl daemon-reload
# Keep configuration and events for troubleshooting and recovery.
printf 'Sidecar parado e desativado. v0.5.8 NAVFIX nao foi alterada.\n'
printf 'Relatorio preservado em /var/lib/blueandme-wheel/observations.csv\n'
