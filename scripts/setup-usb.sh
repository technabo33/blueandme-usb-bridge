#!/usr/bin/env bash
set -euo pipefail
[[ $EUID == 0 ]] || { echo 'Usa sudo.' >&2; exit 1; }
[[ "$(findmnt -n -o FSTYPE /)" != overlay ]] || { echo 'Desativa OverlayFS primeiro.' >&2; exit 1; }
if [[ -e /boot/firmware/config.txt ]]; then
  CFG='/boot/firmware/config.txt'
elif [[ -e /boot/config.txt ]]; then
  CFG='/boot/config.txt'
else
  echo 'Nao encontrei config.txt da Raspberry Pi.' >&2; exit 1
fi
if [[ -e /boot/firmware/cmdline.txt ]]; then
  CMDLINE='/boot/firmware/cmdline.txt'
else
  CMDLINE='/boot/cmdline.txt'
fi
if [[ -f "$CMDLINE" ]] && grep -Eq '(g_serial|g_ether|g_multi)' "$CMDLINE"; then
  echo "CMDLINE ativa outro USB gadget ($CMDLINE). Resolve primeiro o conflito." >&2
  exit 1
fi
if findmnt -n -o OPTIONS --target "$CFG" | grep -qw ro; then
  echo "A particao do boot esta apenas em leitura: $CFG" >&2
  exit 1
fi
if ! grep -Eq '^[[:space:]]*dtoverlay=dwc2([[:space:]]|$)' "$CFG"; then
  cp -a "$CFG" "${CFG}.blueandme-backup.$(date +%Y%m%d%H%M%S)"
  printf '\n[all]\n# BlueAndMe USB device-mode\ndtoverlay=dwc2\n' >> "$CFG"
  echo "Ativado dtoverlay=dwc2 em $CFG"
else
  echo 'dwc2 ja estava configurado.'
fi
printf 'dwc2\n' > /etc/modules-load.d/blueandme-dwc2.conf
