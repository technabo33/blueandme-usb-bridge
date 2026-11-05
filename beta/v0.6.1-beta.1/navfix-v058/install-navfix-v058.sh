#!/usr/bin/env bash
# NAVFIX v0.5.8 EXPERIMENTAL for the original v0.5.6 service only.
# Does not modify systemd, BT config, WAV image, or USB gadget settings.
set -euo pipefail
[[ "$(id -u)" -eq 0 ]] || { echo 'Executa com sudo.' >&2; exit 1; }
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIVE="$(realpath "${1:-$PKG/..}")"
PLUGIN="$LIVE/live_bt_nbd_v056.py"
NEW="$PKG/live_bt_nbd_v056_navfix058.py"
BACKUP="$LIVE/live_bt_nbd_v056.py.stable-v056.backup"
ORIGINAL_SHA='b4e1bae33ac9f018048e759573b86bed679b327e5d30a93f542c8a11e0f91f34'
PATCHED_SHA='e96ce22fa106e6a9f4deb633fb8862826b394d780703444a5c2981513d2cf3e4'
SERVICE='blueandme-bt-v056.service'
sha() { sha256sum "$1" | awk '{print $1}'; }
fail() { echo "ERRO: $*" >&2; exit 1; }

[[ "$(findmnt -n -o FSTYPE /)" != 'overlay' ]] || fail 'OverlayFS ativo. Desativa-o e reinicia antes de instalar.'
[[ -f "$PLUGIN" && -f "$NEW" && -f "$LIVE/start_bt_v056.sh" ]] || fail 'Ficheiros v0.5.6 em falta. Confirma a pasta de instalacao.'
[[ "$(sha "$PLUGIN")" == "$ORIGINAL_SHA" ]] || fail 'O plugin instalado nao e a v0.5.6 original. Nada foi alterado.'
[[ "$(sha "$NEW")" == "$PATCHED_SHA" ]] || fail 'O pacote NAVFIX nao passou a verificacao de integridade.'
systemctl cat "$SERVICE" | grep -Fq "$LIVE/start_bt_v056.sh" || fail 'Este nao e o diretorio utilizado pelo servico v0.5.6.'
systemctl is-active --quiet "$SERVICE" || fail 'O servico v0.5.6 nao esta ativo. Primeiro restaura a v0.5.6.'
if systemctl is-active --quiet blueandme-bt-v057.service; then
  fail 'v0.5.7 ainda esta ativa. Nao vou instalar sobre ela.'
fi
python3 -m py_compile "$NEW"
python3 "$PKG/test_navfix_v058.py" -q

if [[ -f "$BACKUP" ]]; then
  [[ "$(sha "$BACKUP")" == "$ORIGINAL_SHA" ]] || fail 'Copia de recuperacao desconhecida; nao vou substituir.'
else
  cp -p "$PLUGIN" "$BACKUP"
fi

restore() {
  echo 'Falha durante a instalacao NAVFIX. A restaurar v0.5.6 original...' >&2
  systemctl stop "$SERVICE" 2>/dev/null || true
  if [[ -f "$BACKUP" && "$(sha "$BACKUP")" == "$ORIGINAL_SHA" ]]; then
    cp -p "$BACKUP" "$LIVE/.v056-recover.$$"
    mv -f "$LIVE/.v056-recover.$$" "$PLUGIN"
  fi
  rm -f "$LIVE/.live_bt_nbd_v056.py.navfix.$$" || true
  systemctl start "$SERVICE" || true
}
did_stop=0
completed=0
on_exit() {
  code=$?
  trap - EXIT
  if [[ "$code" -ne 0 && "$did_stop" -eq 1 && "$completed" -eq 0 ]]; then
    restore
  fi
  exit "$code"
}
trap on_exit EXIT

echo 'A parar temporariamente v0.5.6; a imagem USB deve estar ejetada.'
did_stop=1
systemctl stop "$SERVICE"
stage="$LIVE/.live_bt_nbd_v056.py.navfix.$$"
cp "$NEW" "$stage"
chown --reference="$PLUGIN" "$stage"
chmod --reference="$PLUGIN" "$stage"
mv -f "$stage" "$PLUGIN"

systemctl start "$SERVICE" || fail 'Nao foi possivel iniciar o servico.'
ready=0
for ((i=0; i<55; i++)); do
  if ! systemctl is-active --quiet "$SERVICE"; then
    break
  fi
  if grep -q '^g_mass_storage ' /proc/modules; then
    ready=1
    break
  fi
  sleep 1
done
[[ "$ready" -eq 1 ]] || fail 'USB virtual nao ficou pronta. A restaurar v0.5.6.'
completed=1
printf '\nNAVFIX v0.5.8 experimental ativo no servico v0.5.6.\n'
printf 'Bluetooth, 48 WAV e scripts de arranque inalterados.\n'
printf 'Reverter: sudo bash %s/rollback-navfix-v058.sh %s\n' "$PKG" "$LIVE"
systemctl --no-pager -l status "$SERVICE" | head -14 || true
