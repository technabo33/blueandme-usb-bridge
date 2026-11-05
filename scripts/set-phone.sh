#!/usr/bin/env bash
set -euo pipefail
[[ $EUID == 0 ]] || { echo 'Usa sudo bash scripts/set-phone.sh AA:BB:CC:DD:EE:FF' >&2; exit 1; }
MAC="${1:-}"
[[ "$MAC" =~ ^([[:xdigit:]]{2}:){5}[[:xdigit:]]{2}$ ]] || { echo 'Endereco Bluetooth invalido.' >&2; exit 1; }
MAC="${MAC^^}"
[[ "$(findmnt -n -o FSTYPE /)" != overlay ]] || { echo 'OverlayFS ativo: desativa e reinicia para persistir alteracoes.' >&2; exit 1; }
INFO="$(bluetoothctl info "$MAC" 2>&1 || true)"
grep -q 'Paired: yes' <<< "$INFO" || { echo 'O telefone ainda nao esta emparelhado.' >&2; exit 1; }
grep -q 'Trusted: yes' <<< "$INFO" || { echo 'Executa primeiro no bluetoothctl: trust '$MAC >&2; exit 1; }
if ! grep -Eq 'Audio Source|0000110a-' <<< "$INFO"; then
  echo 'O dispositivo emparelhado nao anuncia A2DP Audio Source.' >&2
  exit 1
fi
CONFIG='/etc/default/blueandme-bt'
[[ -f "$CONFIG" ]] || { echo 'Primeiro instala o programa.' >&2; exit 1; }
if grep -q '^BM_BT_MAC=' "$CONFIG"; then
  sed -i "s/^BM_BT_MAC=.*/BM_BT_MAC=$MAC/" "$CONFIG"
else
  printf 'BM_BT_MAC=%s\n' "$MAC" >> "$CONFIG"
fi
printf 'Telemovel prioritario configurado. Reinicia o servico com sudo systemctl restart blueandme-bt-v056.service.\n'
