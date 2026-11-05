#!/bin/bash
# Blue&Me 0.5.6 community: supervised foreground; RAM-only logs/PID.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
RUN="${BM_LOG_DIR:-/run/blueandme}"
[[ "$(id -u)" == 0 ]] || { echo 'Executa como root'; exit 1; }
mkdir -p "$RUN"
[[ -f "$DIR/live-long-v050.img" && -f "$DIR/fat_image_v050.py" && -f "$DIR/live_bt_nbd_v056.py" ]] || { echo 'Falta imagem FAT32 ou plugin v0.5.6'; exit 1; }
cd "$DIR"
# The nbdkit Python plugin validates the complete FAT32 image when it loads.
# Avoid running the same cold Python startup + 48-track validation twice.
# If validation fails, nbdkit will exit and the USB gadget will NOT be attached.
echo 'Verificacao FAT32: executada apenas pelo servidor nbdkit.'
server=''
cleanup() {
  trap - EXIT TERM INT
  modprobe -r g_mass_storage 2>/dev/null || true
  nbd-client -d /dev/nbd0 2>/dev/null || true
  if [[ -n "$server" ]]; then
    kill -- "-$server" 2>/dev/null || kill "$server" 2>/dev/null || true
    wait "$server" 2>/dev/null || true
  fi
  rm -f "$RUN/nbdkit-v056.pid"
}
trap 'exit 143' TERM INT
trap cleanup EXIT
if lsmod | grep -q '^g_mass_storage '; then
  echo 'Ja existe um gadget USB em execucao. Para o servico anterior.' >&2
  exit 1
fi
export BM_LOG_DIR="$RUN"
export BM_CAPTURE_USER="${BM_CAPTURE_USER:-pi}"
export BM_PREFILL_SECONDS="${BM_PREFILL_SECONDS:-8}"
export BM_BT_MAC="${BM_BT_MAC:-}"
printf '\n=== ARRANQUE v0.5.6 ===\n' >> "$RUN/reads-bt-v056.log"
printf '\n=== ARRANQUE v0.5.6 ===\n' >> "$RUN/capture-bt-v056.log"
rfkill unblock bluetooth 2>/dev/null || true
modprobe nbd max_part=0
[[ -b /dev/nbd0 ]] || { echo '/dev/nbd0 nao existe' >&2; exit 1; }
setsid nbdkit -f -r -i 127.0.0.1 -p 10809 python "$DIR/live_bt_nbd_v056.py" >> "$RUN/server-bt-v056.log" 2>&1 &
server=$!
printf 'BMSTART nbdkit lancado boot=%ss\n' "$(cut -d' ' -f1 /proc/uptime)"
printf '%s\n' "$server" > "$RUN/nbdkit-v056.pid"
connected=0
for ((i=0; i<100; i++)); do
  if ! kill -0 "$server" 2>/dev/null; then
    echo 'nbdkit terminou; consulta /run/blueandme/server-bt-v056.log' >&2
    exit 1
  fi
  if nbd-client 127.0.0.1 10809 /dev/nbd0 -readonly >> "$RUN/client-bt-v056.log" 2>&1; then
    connected=1
    break
  fi
  sleep 0.5
done
[[ "$connected" == 1 ]] || { echo 'Nao foi possivel estabelecer a ligacao NBD' >&2; exit 1; }
printf 'BMSTART nbd_client ligado boot=%ss\n' "$(cut -d' ' -f1 /proc/uptime)"
blockdev --setra 0 /dev/nbd0
modprobe g_mass_storage file=/dev/nbd0 ro=1 removable=1 stall=0
printf 'Blue&Me v0.5.6: USB ativa, supervisao iniciada boot=%ss\n' "$(cut -d' ' -f1 /proc/uptime)"
# Keep a foreground service so systemd can restart if the NBD server dies.
while true; do
  if ! kill -0 "$server" 2>/dev/null; then
    echo 'nbdkit deixou de funcionar. systemd vai reiniciar.' >&2
    exit 1
  fi
  sleep 5
done
