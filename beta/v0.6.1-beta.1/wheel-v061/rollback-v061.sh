#!/usr/bin/env bash
# Reverte apenas o detetor WheelControl para v0.6.0.
set -Eeuo pipefail
[[ $(id -u) -eq 0 ]] || { echo 'Executa: sudo bash rollback-v061.sh' >&2; exit 1; }
BASE=/opt/blueandme-wheel-v060
TARGET=$BASE/detector.py
BACKUP=/var/lib/blueandme-wheel/rollback-v061/detector-v060.py
SERVICE=blueandme-wheel-v060.service
OLD_HASH=38c56adf3153874eca93b344e7bb68572e9a05886630dfceab1be95b4b65ce63
NEW_HASH=8dd06d0d981b17c3818d35c3b52490a92b4650f9e8ad4b806c9c9ba960608da4
[[ -f "$BACKUP" ]] || { echo 'Nao encontrei o backup v0.6.0. Nenhuma alteracao.' >&2; exit 1; }
[[ $(sha256sum "$BACKUP" | awk '{print $1}') == "$OLD_HASH" ]] || {
    echo 'Backup nao corresponde ao original. Nenhuma alteracao.' >&2; exit 1;
}
[[ -f "$TARGET" ]] || { echo 'Detetor instalado nao existe. Nenhuma alteracao.' >&2; exit 1; }
CURRENT_HASH=$(sha256sum "$TARGET" | awk '{print $1}')
[[ "$CURRENT_HASH" == "$NEW_HASH" || "$CURRENT_HASH" == "$OLD_HASH" ]] || {
    echo 'Existe outra versao do detetor. Nao substituir.' >&2; exit 1;
}
python3 "$BASE/wheelctl.py" auto-off
install -m 0644 "$BACKUP" "$TARGET.new"
mv -f "$TARGET.new" "$TARGET"
systemctl restart "$SERVICE"
sleep 2
systemctl is-active --quiet "$SERVICE" || { echo 'Verifica o servico WheelControl: nao ficou ativo.' >&2; exit 1; }
echo 'Detetor v0.6.0 restaurado. NAVFIX e Bluetooth nao foram alterados.'
