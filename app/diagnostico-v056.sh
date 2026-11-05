#!/bin/bash
set -u
R="${BM_LOG_DIR:-/run/blueandme}"
echo '=== SERVICO ==='
systemctl --no-pager -l status blueandme-bt-v056.service | head -25 || true
echo '=== DISPOSITIVO TRUSTED ==='
CONFIG="/etc/default/blueandme-bt"
if [[ -f "$CONFIG" ]]; then
  # Config installed locally by scripts/install.sh (trusted root-owned file).
  # shellcheck disable=SC1091
  source "$CONFIG"
fi
if [[ -n "${BM_BT_MAC:-}" ]]; then
  bluetoothctl info "$BM_BT_MAC" | grep -E 'Name:|Paired:|Trusted:|Connected:' || true
else
  echo 'Sem MAC primario configurado; pesquisa apenas telefones emparelhados/Trusted.'
fi
echo '=== BLUEALSA ==='
bluealsa-cli list-pcms 2>&1 || true
echo '=== CAPTURA (registos da sessao atual, na RAM) ==='
tail -25 "$R/capture-bt-v056.log" 2>/dev/null || true
echo '=== USB ==='
tail -25 "$R/reads-bt-v056.log" 2>/dev/null || true
echo '=== ALIMENTACAO ==='
if command -v vcgencmd >/dev/null; then vcgencmd get_throttled || true; fi
echo '=== TEMPOS (segundos desde o arranque do kernel) ==='
uptime -s
systemd-analyze time 2>/dev/null || true
grep -E 'FASTPATH|FASTPCM|BT reconnect|Fonte ativa|A2DP arecord' "$R/capture-bt-v056.log" 2>/dev/null | tail -20 || true
