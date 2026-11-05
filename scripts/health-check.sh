#!/usr/bin/env bash
set -uo pipefail
printf '=== BlueAndMe Bridge: diagnostico ===\n'
printf 'Root FS: '; findmnt -n -o FSTYPE / || true
printf 'Service: '; systemctl is-active blueandme-bt-v056.service || true
printf 'Bluetooth: '; systemctl is-active bluetooth.service || true
printf 'BlueALSA: '; systemctl is-active bluealsa.service || true
printf 'USB gadget: '; lsmod | grep -E '^g_mass_storage ' || echo 'Nao carregado'
printf 'NBD: '; lsblk /dev/nbd0 2>/dev/null || true
printf 'RAM logs:\n'; ls -lh /run/blueandme/*v056.log 2>/dev/null || true
printf 'Ultimos eventos:\n'; grep -E 'FASTPCM|A2DP arecord|RESYNC' /run/blueandme/*v056.log 2>/dev/null | tail -12 || true
printf 'Swap:\n'; swapon --show || true
printf 'Boot:\n'; systemd-analyze time 2>/dev/null || true
