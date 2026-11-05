#!/usr/bin/env bash
# Instala APENAS um processo auxiliar, nunca substitui o WAV/BlueALSA/USB.
set -euo pipefail
[[ $(id -u) == 0 ]] || { echo 'Usa sudo bash install-v060.sh' >&2; exit 1; }
DIR=$(cd "$(dirname "$0")" && pwd)
[[ $(findmnt -n -o FSTYPE /) != overlay ]] || { echo 'OverlayFS ativo: desativa e reinicia para persistir instalacao.' >&2; exit 1; }
systemctl is-enabled --quiet blueandme-bt-v056.service || { echo 'v0.5.6/v0.5.8 nao esta ativada. Nao modificar.' >&2; exit 1; }
systemctl is-active --quiet blueandme-bt-v056.service || { echo 'Ponte v0.5.6 nao esta ativa. Nao modificar.' >&2; exit 1; }
python3 -m py_compile "$DIR/wheel/"*.py
python3 -m unittest discover -s "$DIR/tests" -v
mkdir -p /opt/blueandme-wheel-v060 /var/lib/blueandme-wheel
chmod 700 /var/lib/blueandme-wheel
install -m 0644 "$DIR/wheel/avrcp.py" /opt/blueandme-wheel-v060/avrcp.py
install -m 0644 "$DIR/wheel/detector.py" /opt/blueandme-wheel-v060/detector.py
install -m 0644 "$DIR/wheel/monitor.py" /opt/blueandme-wheel-v060/monitor.py
install -m 0644 "$DIR/wheel/wheelctl.py" /opt/blueandme-wheel-v060/wheelctl.py
if [[ ! -e /etc/default/blueandme-wheel ]]; then
  printf 'BM_WHEEL_MODE=observe\n' >/etc/default/blueandme-wheel
  chmod 600 /etc/default/blueandme-wheel
fi
install -m 0644 "$DIR/systemd/blueandme-wheel-v060.service" /etc/systemd/system/blueandme-wheel-v060.service
systemctl daemon-reload
systemctl enable --now blueandme-wheel-v060.service
printf '\nInstalado. Audio e Bluetooth originais nao foram alterados.\n'
printf 'Comandos: sudo python3 /opt/blueandme-wheel-v060/wheelctl.py --help\n'
printf 'Ver log: sudo python3 /opt/blueandme-wheel-v060/wheelctl.py report\n'
