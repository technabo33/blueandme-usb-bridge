#!/usr/bin/env python3
"""Send BlueZ MediaPlayer1 transport commands to the active, trusted A2DP phone.

No MAC, private path or network credentials are compiled into this module.
Only run this from an explicit local action or an opt-in monitoring service.
"""
from __future__ import annotations
import re
import subprocess
from pathlib import Path

MAC = re.compile(r'\b(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}\b')
PLAYER = re.compile(r'/org/bluez/hci\d+/dev_(?:[0-9A-Fa-f]{2}_){5}[0-9A-Fa-f]{2}/player\d+')
LOG = Path('/run/blueandme/capture-bt-v056.log')
COMMANDS = {'next': 'Next', 'previous': 'Previous', 'play': 'Play', 'pause': 'Pause'}

class AVRCPError(RuntimeError):
    pass


def run(args, timeout=7):
    try:
        return subprocess.run(args, capture_output=True, text=True,
                              timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AVRCPError('O comando Bluetooth falhou ou excedeu o tempo limite.') from exc


def last_active_mac(log=LOG):
    """Optionally prefer the active source in the currently running bridge log."""
    try:
        with log.open('rb') as f:
            f.seek(0, 2)
            end = f.tell()
            f.seek(max(0, end - 65536))
            raw = f.read().decode('utf-8', errors='ignore')
    except OSError:
        return None
    values = re.findall(r'Fonte ativa:\s*((?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2})\b', raw)
    return values[-1].upper() if values else None


def player_address(player_path):
    m = re.search(r'/dev_((?:[0-9A-Fa-f]{2}_){5}[0-9A-Fa-f]{2})/', player_path)
    return m.group(1).replace('_', ':').upper() if m else None


def available_players(runner=run):
    result = runner(['busctl', '--system', 'tree', 'org.bluez'], timeout=7)
    if result.returncode:
        raise AVRCPError('Nao foi possivel consultar os players Bluetooth no D-Bus.')
    return sorted(set(PLAYER.findall(result.stdout)))


def trusted_and_connected(mac, runner=run):
    result = runner(['bluetoothctl', '--timeout', '5', 'info', mac], timeout=8)
    if result.returncode:
        return False
    value = result.stdout
    return ('Paired: yes' in value and 'Trusted: yes' in value and
            'Connected: yes' in value)


def choose_player(players, preferred=None, runner=run):
    """Only accept one known, connected and trusted media player."""
    devices = [(path, player_address(path)) for path in players]
    devices = [(p, mac) for p, mac in devices if mac]
    if preferred:
        devices = [(p, mac) for p, mac in devices if mac == preferred.upper()]
    devices = [(p, mac) for p, mac in devices if trusted_and_connected(mac, runner)]
    if len(devices) != 1:
        raise AVRCPError('Nao existe exatamente um player autorizado e ligado. Verifica o telefone emparelhado.')
    return devices[0][0]


def status(runner=run, log=LOG):
    players = available_players(runner)
    path = choose_player(players, last_active_mac(log), runner)
    return path is not None


def send(command, runner=run, log=LOG):
    if command not in COMMANDS:
        raise AVRCPError('Comando desconhecido.')
    players = available_players(runner)
    path = choose_player(players, last_active_mac(log), runner)
    result = runner(['busctl', '--system', 'call', 'org.bluez', path,
                     'org.bluez.MediaPlayer1', COMMANDS[command]], timeout=6)
    if result.returncode:
        raise AVRCPError('O player Bluetooth recusou o comando AVRCP.')
    return True
