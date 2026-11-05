#!/usr/bin/env python3
"""Manual AVRCP test, status and opt-in controls. Must be invoked locally as root."""
import os
import sys
import subprocess
from pathlib import Path
from avrcp import AVRCPError, status, send
from monitor import CONF, STATE_CSV, STATE_DIR, mode


HELP = '''Uso: sudo python3 /opt/blueandme-wheel-v060/wheelctl.py <acao>
  status                 verifica player BlueZ (nao muda Spotify)
  next                   comando manual Seguinte
  previous               comando manual Anterior
  report                 mostra resumo anonimizado guardado no microSD
  auto-on --confirmed    ativa reconhecimento automatico experimental
  auto-off               desativa imediatamente os comandos automaticos
'''


def require_root():
    if os.geteuid() != 0:
        raise ValueError('Executa com sudo.')


def set_mode(value):
    CONF.parent.mkdir(parents=True, exist_ok=True)
    temp = CONF.with_name(CONF.name + '.tmp')
    temp.write_text('BM_WHEEL_MODE=' + value + '\n', encoding='ascii')
    os.chmod(temp, 0o600)
    os.replace(temp, CONF)
    print('Modo AVRCP:', value)


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ('-h', '--help'):
        print(HELP)
        return 0
    try:
        require_root()
        action = args[0]
        if action == 'status':
            print('Modo atual:', mode())
            print('Player AVRCP do telefone ligado:', 'disponivel' if status() else 'indisponivel')
        elif action in ('next', 'previous'):
            print('A enviar comando manual ao telemovel ligado...')
            send(action)
            STATE_DIR.mkdir(parents=True, exist_ok=True)
            marker = STATE_DIR / ('manual-' + action + '-ok')
            marker.write_text('D-Bus aceitou; confirmar no Spotify\n', encoding='utf-8')
            print('D-Bus aceitou o comando. CONFIRMA se o Spotify realmente mudou.')
        elif action == 'report':
            if STATE_CSV.exists():
                rows = STATE_CSV.read_text(encoding='utf-8').splitlines()
                print('\n'.join(rows[-25:]))
            else:
                print('Ainda sem eventos guardados.')
        elif action == 'auto-off':
            set_mode('observe')
        elif action == 'auto-on':
            if len(args) != 2 or args[1] != '--confirmed':
                raise ValueError('Esta funcao requer auto-on --confirmed (apenas apos testar next/previous).')
            for name in ('manual-next-ok', 'manual-previous-ok'):
                if not (STATE_DIR / name).exists():
                    raise ValueError('Primeiro testa next e previous no telemovel ligado.')
            set_mode('auto')
            print('Experimental: so classificacoes conservadoras dao comandos. Pode haver falsos positivos.')
            print('Podes desativar a qualquer momento: sudo python3 /opt/blueandme-wheel-v060/wheelctl.py auto-off')
        else:
            raise ValueError('Acao desconhecida. Usa --help.')
        return 0
    except (AVRCPError, ValueError, OSError) as exc:
        # No MAC or raw D-Bus output in exceptions presented by our API.
        print('ERRO:', str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
