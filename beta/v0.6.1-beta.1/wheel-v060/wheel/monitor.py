#!/usr/bin/env python3
"""Sidecar for Blue&Me NAVFIX v0.5.8. Never modifies the bridge or USB stream."""
from __future__ import annotations
import csv
import os
from pathlib import Path
import signal
import sys
import time
from detector import Detector
from avrcp import AVRCPError, send

READ_LOG = Path('/run/blueandme/reads-bt-v056.log')
STATE_DIR = Path('/var/lib/blueandme-wheel')
STATE_CSV = STATE_DIR / 'observations.csv'
CONF = Path('/etc/default/blueandme-wheel')
FIELDS = ('uptime_s', 'event', 'direction', 'from_wav', 'to_wav', 'result')


def mode():
    """Read configuration on every event so disabling auto doesn't need reboot."""
    try:
        text = CONF.read_text('utf-8')
    except OSError:
        return 'observe'
    for line in text.splitlines():
        if line.strip() == 'BM_WHEEL_MODE=auto':
            return 'auto'
    return 'observe'


def record(kind, event=None, result=''):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(STATE_DIR, 0o700)
    exists = STATE_CSV.exists() and STATE_CSV.stat().st_size > 0
    with STATE_CSV.open('a', newline='', encoding='utf-8') as f:
        os.chmod(STATE_CSV, 0o600)
        writer = csv.DictWriter(f, FIELDS)
        if not exists:
            writer.writeheader()
        writer.writerow({'uptime_s': f'{time.monotonic():.1f}',
                         'event': kind,
                         'direction': event.direction if event else '',
                         'from_wav': event.old if event else '',
                         'to_wav': event.new if event else '',
                         'result': result})
        f.flush()
        os.fsync(f.fileno())


def run_monitor():
    detector = Detector()
    record('START', result='mode-noted-on-events')
    while True:
        if not READ_LOG.exists():
            time.sleep(1.0)
            continue
        with READ_LOG.open('r', encoding='utf-8', errors='replace') as f:
            # Ignore old events. This prevents accidental AVRCP on service restart.
            f.seek(0, os.SEEK_END)
            ino = os.fstat(f.fileno()).st_ino
            while True:
                line = f.readline()
                if line:
                    event = detector.process(line)
                    if event is None:
                        continue
                    record('TRACK_CHANGE_PROBABLE', event, result='NOT_CONFIRMED')
                    if mode() != 'auto':
                        continue
                    # Never send from the read callback; this is a separate process.
                    try:
                        send(event.direction)
                        record('AVRCP_SENT', event, result='busctl_ok_not_spotify_ack')
                    except AVRCPError:
                        record('AVRCP_FAILED', event, result='bluetooth_error')
                    continue
                time.sleep(0.20)
                try:
                    st = READ_LOG.stat()
                except FileNotFoundError:
                    break
                if st.st_ino != ino or st.st_size < f.tell():
                    detector.reset()
                    break


if __name__ == '__main__':
    try:
        run_monitor()
    except KeyboardInterrupt:
        pass
