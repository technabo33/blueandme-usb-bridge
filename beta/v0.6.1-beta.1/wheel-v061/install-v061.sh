#!/usr/bin/env bash
# Instala a deteccao Next/Previous SEM alterar o motor USB/BT NAVFIX.
set -Eeuo pipefail

[[ $(id -u) -eq 0 ]] || { echo 'Executa: sudo bash install-v061.sh' >&2; exit 1; }
DIR=$(cd "$(dirname "$0")" && pwd)
BASE=/opt/blueandme-wheel-v060
TARGET=$BASE/detector.py
BACKUP_DIR=/var/lib/blueandme-wheel/rollback-v061
BACKUP=$BACKUP_DIR/detector-v060.py
SERVICE=blueandme-wheel-v060.service
OLD_HASH=38c56adf3153874eca93b344e7bb68572e9a05886630dfceab1be95b4b65ce63
NEW_HASH=8dd06d0d981b17c3818d35c3b52490a92b4650f9e8ad4b806c9c9ba960608da4

if [[ $(findmnt -n -o FSTYPE /) == overlay ]]; then
    echo 'OverlayFS ativo: nao e seguro persistir esta atualizacao.' >&2
    exit 1
fi
systemctl is-active --quiet blueandme-bt-v056.service || { echo 'A ponte USB/BT nao esta ativa. Nao alterar.' >&2; exit 1; }
systemctl is-active --quiet "$SERVICE" || { echo 'WheelControl v0.6.0 nao esta ativo. Nao alterar.' >&2; exit 1; }
[[ -f "$TARGET" && -f "$BASE/monitor.py" && -f "$BASE/wheelctl.py" ]] || {
    echo 'WheelControl v0.6.0 incompleto. Nao alterar.' >&2; exit 1;
}
python3 -m py_compile "$DIR/detector.py"
python3 -m unittest discover -s "$DIR/tests" -p 'test_*.py' -q

CURRENT_HASH=$(sha256sum "$TARGET" | awk '{print $1}')
SOURCE_HASH=$(sha256sum "$DIR/detector.py" | awk '{print $1}')
[[ "$SOURCE_HASH" == "$NEW_HASH" ]] || { echo 'ERRO: pacote alterado ou corrompido.' >&2; exit 1; }
[[ "$CURRENT_HASH" == "$OLD_HASH" || "$CURRENT_HASH" == "$NEW_HASH" ]] || {
    echo 'O detetor instalado nao e a v0.6.0 esperada. Nao o vou substituir.' >&2
    echo 'SHA256 atual: '"$CURRENT_HASH" >&2
    exit 1
}

# Desligar a automacao ANTES de modificar codigo, inclusive se ja estiver instalada.
python3 "$BASE/wheelctl.py" auto-off

if [[ "$CURRENT_HASH" == "$NEW_HASH" ]]; then
    echo 'v0.6.1 ja instalada. Modo automatico desligado por seguranca.'
    exit 0
fi

install -d -m 0700 "$BACKUP_DIR"
if [[ -e "$BACKUP" ]]; then
    [[ $(sha256sum "$BACKUP" | awk '{print $1}') == "$OLD_HASH" ]] || {
        echo 'Backup v0.6.0 divergente: nao substituir.' >&2; exit 1;
    }
else
    install -m 0600 "$TARGET" "$BACKUP"
fi

install -m 0644 "$DIR/detector.py" "$TARGET.new"
mv -f "$TARGET.new" "$TARGET"
if ! systemctl restart "$SERVICE"; then
    echo 'Falha a reiniciar. A restaurar o detetor original.' >&2
    install -m 0644 "$BACKUP" "$TARGET"
    systemctl restart "$SERVICE" || true
    exit 1
fi
sleep 2
if ! systemctl is-active --quiet "$SERVICE"; then
    echo 'Servico nao ficou ativo. A restaurar o detetor original.' >&2
    install -m 0644 "$BACKUP" "$TARGET"
    systemctl restart "$SERVICE" || true
    exit 1
fi
printf '\nBlue&Me WheelControl v0.6.1 instalada.\n'
printf 'USB e Bluetooth NAVFIX nao foram alterados.\n'
printf 'Modo atual: OBSERVE (nao envia comandos AVRCP automaticos).\n'
printf 'Para ativar apos teste: sudo python3 %s/wheelctl.py auto-on --confirmed\n' "$BASE"
printf 'Para voltar atras: sudo bash %s/rollback-v061.sh\n' "$DIR"
