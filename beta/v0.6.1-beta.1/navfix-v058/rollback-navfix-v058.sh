#!/usr/bin/env bash
set -euo pipefail
[[ "$(id -u)" -eq 0 ]] || { echo 'Executa com sudo.' >&2; exit 1; }
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIVE="$(realpath "${1:-$PKG/..}")"
PLUGIN="$LIVE/live_bt_nbd_v056.py"
BACKUP="$LIVE/live_bt_nbd_v056.py.stable-v056.backup"
ORIGINAL_SHA='b4e1bae33ac9f018048e759573b86bed679b327e5d30a93f542c8a11e0f91f34'
[[ "$(findmnt -n -o FSTYPE /)" != 'overlay' ]] || { echo 'OverlayFS ativo; a alteracao nao persistiria.' >&2; exit 1; }
[[ -f "$BACKUP" ]] || { echo 'Falta a copia da v0.5.6.' >&2; exit 1; }
[[ "$(sha256sum "$BACKUP" | awk '{print $1}')" == "$ORIGINAL_SHA" ]] || { echo 'Backup v0.5.6 nao reconhecido.' >&2; exit 1; }
systemctl stop blueandme-bt-v056.service
cp -p "$BACKUP" "$LIVE/.v056-recover.$$"
mv -f "$LIVE/.v056-recover.$$" "$PLUGIN"
systemctl start blueandme-bt-v056.service
printf 'Plugin original v0.5.6 restaurado. Bluetooth/configuracao/USB mantidos.\n'
systemctl --no-pager -l status blueandme-bt-v056.service | head -12 || true
