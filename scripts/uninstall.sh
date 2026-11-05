#!/usr/bin/env bash
set -euo pipefail
[[ $EUID == 0 ]] || { echo 'Usa sudo bash scripts/uninstall.sh' >&2; exit 1; }
[[ "$(findmnt -n -o FSTYPE /)" != overlay ]] || { echo 'Desativa OverlayFS e reinicia antes de desinstalar.' >&2; exit 1; }
systemctl disable --now blueandme-bt-v056.service 2>/dev/null || true
if [[ -f /etc/systemd/system/blueandme-bt-v056.service ]] && grep -q '/opt/blueandme-bridge' /etc/systemd/system/blueandme-bt-v056.service; then
  rm /etc/systemd/system/blueandme-bt-v056.service
fi
systemctl daemon-reload
cat <<'EOF'
O servico comunitario foi removido. Foram preservados:
  /opt/blueandme-bridge (codigo e imagem)
  /etc/default/blueandme-bt (configuracao)
  Configuracao dwc2 no arranque e BlueALSA (podem ser usados por outros projetos)
Remove-os manualmente apenas se tiveres a certeza de que ja nao sao necessarios.
EOF
