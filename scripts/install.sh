#!/usr/bin/env bash
# Instala a versao comunitaria. Nunca altera a instalacao privada existente.
set -euo pipefail
[[ $EUID == 0 ]] || { echo 'Usa: sudo bash scripts/install.sh' >&2; exit 1; }
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT='/opt/blueandme-bridge'
SERVICE='blueandme-bt-v056.service'
RUN_USER="${BM_INSTALL_USER:-${SUDO_USER:-}}"
HOURS="${BM_HOURS:-24}"

[[ -n "$RUN_USER" && "$RUN_USER" != root ]] || { echo 'Falta utilizador. Experimenta: sudo BM_INSTALL_USER=pi bash scripts/install.sh' >&2; exit 1; }
id "$RUN_USER" >/dev/null 2>&1 || { echo "Utilizador inexistente: $RUN_USER" >&2; exit 1; }
[[ "$HOURS" =~ ^([1-9]|[1-3][0-9]|4[0-8])$ ]] || { echo 'BM_HOURS deve ser 1 a 48' >&2; exit 1; }
if [[ "$(findmnt -n -o FSTYPE /)" == 'overlay' ]]; then
  echo 'OverlayFS ativo. Desativa-o temporariamente via sudo raspi-config, reinicia e volta a instalar.' >&2
  exit 1
fi
if [[ -e /etc/systemd/system/blueandme-bt-v056.service || -e /lib/systemd/system/blueandme-bt-v056.service ]]; then
  if ! grep -q '/opt/blueandme-bridge' /etc/systemd/system/blueandme-bt-v056.service 2>/dev/null; then
    echo 'Foi encontrada uma v0.5.6 nao-comunitaria instalada. Para proteger a versao funcional, o instalador nao a substitui.' >&2
    echo 'Usa um SD novo ou desinstala manualmente a versao antiga depois de efetuar backup.' >&2
    exit 1
  fi
fi
if lsmod | grep -q '^g_mass_storage '; then
  echo 'Ja existe um dispositivo USB mass storage ativo. Para o servico antigo antes de continuar.' >&2
  exit 1
fi

printf '\n[1/6] A instalar dependencias (requer Internet)...\n'
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
  python3 bluez bluez-alsa-utils libasound2-plugin-bluez alsa-utils \
  nbd-client nbdkit nbdkit-plugin-python rfkill kmod git
for command in python3 nbdkit nbd-client bluetoothctl bluealsa bluealsa-cli arecord modprobe; do
  command -v "$command" >/dev/null || { echo "Dependencia ausente: $command" >&2; exit 1; }
done

printf '\n[2/6] A copiar codigo...\n'
install -d -m0755 "$ROOT"
install -m0644 "$REPO_DIR/app/fat_image_v050.py" "$ROOT/"
install -m0644 "$REPO_DIR/app/live_bt_nbd_v056.py" "$ROOT/"
install -m0755 "$REPO_DIR/app/start_bt_v056.sh" "$ROOT/"
install -m0755 "$REPO_DIR/app/diagnostico-v056.sh" "$ROOT/"
python3 -m py_compile "$ROOT/fat_image_v050.py" "$ROOT/live_bt_nbd_v056.py"
bash -n "$ROOT/start_bt_v056.sh"

printf '\n[3/6] A preparar imagem FAT32 sparse...\n'
IMAGE="$ROOT/live-long-v050.img"
if [[ -e "$IMAGE" ]]; then
  echo 'Imagem existente preservada. A verificar integridade...'
  python3 - "$ROOT" <<'PYI'
import sys
sys.path.insert(0, sys.argv[1])
from fat_image_v050 import image_regions
n = len(image_regions(sys.argv[1] + '/live-long-v050.img'))
print('WAV validos:', n)
PYI
else
  python3 "$ROOT/fat_image_v050.py" "$IMAGE" --hours "$HOURS"
fi

printf '\n[4/6] A criar configuracao local...\n'
CFG='/etc/default/blueandme-bt'
if [[ -f "$CFG" ]]; then
  echo "Configuracao $CFG existente preservada. Confirma BM_CAPTURE_USER manualmente."
  chmod 0600 "$CFG"
else
  cat > "$CFG" <<EOF
# Ficheiro local: NAO publicar no GitHub
BM_CAPTURE_USER=$RUN_USER
BM_BT_MAC=
BM_PREFILL_SECONDS=8
BM_BT_FIRST_ATTEMPT_DELAY=1
EOF
  chmod 0600 "$CFG"
fi
usermod -a -G audio "$RUN_USER"

printf '\n[5/6] A preparar BlueALSA...\n'
if ! systemctl cat bluealsa.service >/dev/null 2>&1; then
  install -m0644 "$REPO_DIR/systemd/bluealsa-fallback.service" /etc/systemd/system/bluealsa.service
  echo 'Servico BlueALSA de recurso instalado com -p a2dp-sink.'
else
  echo 'Servico bluealsa.service existente preservado. Confirma que suporta -p a2dp-sink.'
fi
systemctl daemon-reload
systemctl enable --now bluetooth.service
systemctl enable --now bluealsa.service

printf '\n[6/6] A preparar modo USB OTG e servico...\n'
bash "$REPO_DIR/scripts/setup-usb.sh"
install -m0644 "$REPO_DIR/systemd/blueandme-bt.service" "/etc/systemd/system/$SERVICE"
systemctl daemon-reload
systemctl enable "$SERVICE"
echo
printf '%s\n' 'INSTALACAO CONCLUIDA. Reinicia: sudo reboot' \
  'Apos o reboot, emparelha o telemovel e configura o MAC (ver INSTALL.pt-PT.md).' \
  "Diagnostico: sudo bash $ROOT/diagnostico-v056.sh"
