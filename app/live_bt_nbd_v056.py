#!/usr/bin/env python3
"""Blue&Me Bridge v0.5.6: A2DP to sparse FAT32 multi-track USB mass storage.

24h by default in 48 x 30-minute WAV files. Limited by declared track count.
Neither Blue&Me gapless switching nor read-ahead/cache can be guaranteed.
"""
import os
import re
import select
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

API_VERSION = 2
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
from fat_image_v050 import image_regions, TRACK_SECONDS

IMG = BASE / 'live-long-v050.img'
LOG_DIR = Path(os.environ.get('BM_LOG_DIR', '/run/blueandme'))
LOG_DIR.mkdir(parents=True, exist_ok=True)
READ_LOG = LOG_DIR / 'reads-bt-v056.log'
CAPTURE_LOG = LOG_DIR / 'capture-bt-v056.log'
PREFERENCE_FILE = BASE / 'prefer-phone.txt'
RATE = 44100
FRAME_BYTES = 4
BPS = RATE * FRAME_BYTES
RING_SECONDS = 40
RING_SIZE = RING_SECONDS * BPS
PREFILL_SECONDS = max(2, min(20, int(os.environ.get('BM_PREFILL_SECONDS', '8'))))
PREFILL_BYTES = PREFILL_SECONDS * BPS
CAPTURE_USER = os.environ.get('BM_CAPTURE_USER', 'pi')
FIRST_PHONE = os.environ.get('BM_BT_MAC', '').strip().upper()
MAC_RE = re.compile(r'^[0-9A-F]{2}(?::[0-9A-F]{2}){5}$')
AUDIO_REGIONS = image_regions(IMG)
VIRTUAL_TRACK_BYTES = TRACK_SECONDS * BPS


def log(path, message):
    with path.open('a', encoding='utf-8') as f:
        f.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")} {message}\n')


def btctl(*args, timeout=8):
    try:
        p = subprocess.run(['bluetoothctl', '--timeout', str(timeout), *args],
                           capture_output=True, text=True, timeout=timeout + 3,
                           check=False)
        return p.stdout + '\n' + p.stderr
    except (OSError, subprocess.TimeoutExpired) as e:
        log(CAPTURE_LOG, f'BlueZ indisponivel ({args[0] if args else "?"}): {e}')
        return ''


def paired_trusted():
    """Only pre-paired, trusted A2DP-capable phones. Never auto-authorize strangers."""
    listing = btctl('devices', 'Paired')
    macs = re.findall(r'^Device\s+([0-9A-Fa-f:]{17})\s', listing, re.MULTILINE)
    trusted = []
    for address in macs:
        address = address.upper()
        info = btctl('info', address)
        if 'Paired: yes' not in info or 'Trusted: yes' not in info:
            continue
        # Standard A2DP Source UUID (phones send music into the Pi A2DP sink).
        if not (re.search(r'0000110a-', info, re.I) or
                'Audio Source' in info):
            continue
        trusted.append((address, 'Connected: yes' in info))
    trusted.sort(key=lambda item: (item[0] != FIRST_PHONE, item[0]))
    return trusted


class Capture:
    def __init__(self):
        self.lock = threading.Lock()
        self.ring = bytearray(RING_SIZE)
        self.total = 0
        self.generation = 0
        self.active = False
        self.last_rx = 0.0
        self.phone = None

    def clear(self, reason='no audio'):
        with self.lock:
            if self.total == 0 and not self.active:
                return
            self.ring[:] = bytes(RING_SIZE)
            self.total = 0
            self.active = False
            self.last_rx = 0
            self.generation += 1
        log(CAPTURE_LOG, f'Buffer em RAM limpo: {reason}')

    def new_phone(self, address):
        self.clear('troca de origem Bluetooth')
        with self.lock:
            self.phone = address
            self.generation += 1
        log(CAPTURE_LOG, f'Fonte ativa: {address} boot={time.monotonic():.1f}s')

    def add(self, raw):
        count = len(raw) // FRAME_BYTES * FRAME_BYTES
        if not count:
            return
        raw = raw[:count]
        if len(raw) > RING_SIZE:
            raw = raw[-RING_SIZE:]
        with self.lock:
            write_pos = self.total % RING_SIZE
            first = min(len(raw), RING_SIZE - write_pos)
            self.ring[write_pos:write_pos + first] = raw[:first]
            if first < len(raw):
                self.ring[:len(raw) - first] = raw[first:]
            self.total += len(raw)
            self.last_rx = time.monotonic()
            self.active = True

    def get(self, source_offset, length):
        result = bytearray(length)  # Silence for anything unavailable.
        with self.lock:
            if not self.active:
                return bytes(result), 0
            low = max(0, self.total - RING_SIZE)
            a = max(source_offset, low)
            b = min(source_offset + length, self.total)
            if b <= a:
                return bytes(result), 0
            pos = a % RING_SIZE
            size = b - a
            first = min(size, RING_SIZE - pos)
            out_start = a - source_offset
            result[out_start:out_start + first] = self.ring[pos:pos + first]
            if size > first:
                result[out_start + first:out_start + size] = self.ring[:size - first]
            return bytes(result), size


CAP = Capture()


def preferred_phone():
    try:
        p = PREFERENCE_FILE.read_text(encoding='ascii').strip().upper()
        return p if MAC_RE.fullmatch(p) else None
    except (OSError, UnicodeError):
        return None


def choose_phone(known, current):
    """Keep the active connected phone; allow explicit handover by preference file."""
    connected = {mac for mac, up in known if up}
    requested = preferred_phone()
    if requested and requested in connected:
        return requested
    if current in connected:
        return current
    for mac, up in known:
        if up:
            return mac
    return None


# Never execute slow bluetoothctl subprocesses in the PCM reader thread.
# On the Pi Zero W these calls can stall for many seconds, filling the small
# ALSA capture buffer and triggering "overrun!!!" errors.
KNOWN_PHONES_LOCK = threading.Lock()
KNOWN_PHONES = []
BT_POWER_READY = threading.Event()
FASTPATH_DONE = threading.Event()
FAST_CAPTURE_STARTED = threading.Event()


def is_authorized_a2dp(info):
    """Require a previously paired and Trusted A2DP Source (not just a known MAC)."""
    return ('Paired: yes' in info and 'Trusted: yes' in info and
            ('Audio Source' in info or re.search(r'0000110a-', info, re.I)))


def scan_trusted_phones():
    # Let the trusted primary phone take the fast connection path first.
    # The periodic full scan still enables other previously authorized phones.
    FASTPATH_DONE.wait(timeout=12)
    time.sleep(5)
    while True:
        try:
            found = paired_trusted()
            with KNOWN_PHONES_LOCK:
                KNOWN_PHONES[:] = found
        except Exception as e:
            log(CAPTURE_LOG, f'Falha no scanner de telemoveis: {e}')
        time.sleep(5)


def reconnect_worker():
    """Best-effort reconnection to pre-trusted phones without overlapping calls.

    The phone (A2DP source) may only reconnect when it initiates the link.
    Some Android phones refuse an outbound request from the Pi (A2DP sink).
    Prefer the remote A2DP-source profile which connected reliably to the
    original reference Android handset. Keep an occasional generic fallback for other phones.
    """
    # Fast lane: avoid the costly `bluetoothctl devices Paired` + info sweep
    # for the already configured primary phone. Never trust the MAC by itself:
    # require Paired=yes, Trusted=yes and A2DP Source before selecting it.
    BT_POWER_READY.wait(timeout=9)
    if FIRST_PHONE and MAC_RE.fullmatch(FIRST_PHONE):
        primary = btctl('info', FIRST_PHONE, timeout=6)
        if is_authorized_a2dp(primary):
            with KNOWN_PHONES_LOCK:
                if not any(mac == FIRST_PHONE for mac, _ in KNOWN_PHONES):
                    KNOWN_PHONES.insert(0, (FIRST_PHONE, 'Connected: yes' in primary))
            log(CAPTURE_LOG, f'FASTPATH dispositivo Trusted verificado: {FIRST_PHONE} '
                             f'boot={time.monotonic():.1f}s')
            threading.Thread(target=fast_pcm_watcher, args=(FIRST_PHONE,),
                             name='BlueALSA-FastPCM', daemon=True).start()
        else:
            log(CAPTURE_LOG, f'FASTPATH indisponivel/nao autorizado: {FIRST_PHONE}; '
                             'scanner completo assumira a deteccao')
    FASTPATH_DONE.set()
    next_attempt = time.monotonic() + max(0, min(20, int(
        os.environ.get('BM_BT_FIRST_ATTEMPT_DELAY', '1'))))
    attempt = 0
    while True:
        now = time.monotonic()
        if now < next_attempt:
            time.sleep(min(2, next_attempt - now))
            continue
        with KNOWN_PHONES_LOCK:
            trusted = list(KNOWN_PHONES)
        # Incoming Android connections always take precedence.
        if not trusted:
            # Initial paired device discovery can run for several seconds.
            # Check promptly rather than adding a further 8s penalty.
            next_attempt = time.monotonic() + 2
            continue
        if any(connected for _, connected in trusted):
            next_attempt = time.monotonic() + 8
            continue
        candidates = [mac for mac, connected in trusted if not connected]
        mac = candidates[attempt % len(candidates)]
        # No simultaneous requests: this worker is the sole outbound connector.
        # ConnectProfile uses the REMOTE audio-source UUID of the phone.
        # First attempt is always A2DP; generic is tried once every fourth
        # full round of target devices, preserving a fallback for other phones.
        profile = (attempt // max(1, len(candidates))) % 4 != 3
        args = ('connect', mac, 'a2dp-source') if profile else ('connect', mac)
        attempt += 1
        log(CAPTURE_LOG, f'BT reconnect tentativa={attempt} alvo={mac} '
                         f'modo={"a2dp-source" if profile else "generico"} '
                         f'boot={time.monotonic():.1f}s')
        response = btctl(*args, timeout=14).strip().replace('\n', ' | ')
        log(CAPTURE_LOG, f'BT reconnect resposta: {response[:500] or "nenhuma"}')
        time.sleep(4)
        info = btctl('info', mac, timeout=5)
        connected = 'Connected: yes' in info
        log(CAPTURE_LOG, f'BT reconnect resultado {mac}: '
                         f'{"Connected: yes" if connected else "Connected: no"} '
                         f'boot={time.monotonic():.1f}s')
        if connected:
            # Don't wait for the slow full scanner to refresh the connection.
            with KNOWN_PHONES_LOCK:
                KNOWN_PHONES[:] = [(m, (True if m == mac else up))
                                  for m, up in KNOWN_PHONES]
        if not connected:
            log(CAPTURE_LOG, 'NOTA: Android pode exigir que o telemovel inicie '
                             'a ligacao A2DP. O Raspberry continua a aceitar '
                             'ligacoes dos dispositivos Trusted.')
        # Keep attempts far apart so a BlueZ request has time to settle.
        # This worker waits for each bluetoothctl subprocess to finish and
        # checks status before scheduling another attempt. Avoid excessive
        # 25-second idle delays after failures, but do not spam BlueZ.
        next_attempt = time.monotonic() + (10 if connected else 12)


def fast_pcm_watcher(mac):
    """Promote a verified paired/trusted primary phone when its BlueALSA
    PCM is ready, without waiting for a slower bluetoothctl info scan.

    The existing trusted-phone scanner retains normal reconnection logic.
    """
    deadline = time.monotonic() + 90
    reported = False
    while time.monotonic() < deadline and not FAST_CAPTURE_STARTED.is_set():
        if pcm_ready(mac):
            with KNOWN_PHONES_LOCK:
                for i, (address, connected) in enumerate(KNOWN_PHONES):
                    if address == mac:
                        KNOWN_PHONES[i] = (mac, True)
                        break
                else:
                    KNOWN_PHONES.insert(0, (mac, True))
            if not reported:
                log(CAPTURE_LOG, f'FASTPCM A2DP pronto: {mac} '
                                 f'boot={time.monotonic():.1f}s; '
                                 'captura desbloqueada')
                reported = True
        # Repeat briefly while launching arecord so a concurrent slow scan
        # cannot overwrite a fresh PCM-ready result with a stale BT status.
        time.sleep(1.5 if reported else 1.0)
    if not reported:
        log(CAPTURE_LOG, f'FASTPCM sem resultado no prazo: {mac}; '
                         'scanner normal preservado')


def pcm_ready(mac):
    """Use BlueALSA 4.3.1's CLI to wait for the A2DP PCM DBus object.

    Fall back to controlled arecord retries only if bluealsa-cli is absent.
    """
    try:
        p = subprocess.run(['bluealsa-cli', 'list-pcms'],
                           capture_output=True, text=True, timeout=5,
                           check=False)
    except FileNotFoundError:
        return True
    except subprocess.TimeoutExpired:
        return False
    expected = f'/dev_{mac.replace(":", "_")}/a2dpsnk/source'
    return p.returncode == 0 and expected.lower() in p.stdout.lower()


def configure_bluetooth():
    """Power on early; keep device non-discoverable/non-pairable by default.

    Signal the fast reconnect worker as soon as power-on has been requested.
    Other authorized phones are still found by the normal scanner.
    """
    try:
        result = btctl('power', 'on', timeout=6).strip().replace('\n', ' | ')
        log(CAPTURE_LOG, f'BT setup power on: {result[:240]}')
    finally:
        BT_POWER_READY.set()
    for args in [('discoverable', 'off'), ('pairable', 'off')]:
        result = btctl(*args, timeout=6).strip().replace('\n', ' | ')
        log(CAPTURE_LOG, f'BT setup {" ".join(args)}: {result[:240]}')


def capture_manager():
    """Capture ONE phone at a time. Slow BlueZ calls run in other threads."""
    # Previously three serial bluetoothctl calls (up to 8s each) delayed
    # phone discovery; do not put them on the main capture thread.
    threading.Thread(target=configure_bluetooth,
                     name='BlueZ-Setup', daemon=True).start()
    threading.Thread(target=scan_trusted_phones,
                     name='BlueZ-Scanner', daemon=True).start()
    threading.Thread(target=reconnect_worker,
                     name='BlueZ-Reconnect', daemon=True).start()
    log(CAPTURE_LOG, 'v0.5.6: FASTPATH primaria, A2DP-first, FASTPCM, scanner secundario; boot=%.1fs' % time.monotonic())
    selected = None
    process = None
    last_packet = 0.0
    pending = b''
    next_pcm_check = 0.0
    next_capture_try = 0.0
    capture_failures = 0
    pcm_silence_start = None
    pcm_silence_cleared = False
    while True:
        now = time.monotonic()
        with KNOWN_PHONES_LOCK:
            last_known = list(KNOWN_PHONES)
        desired = choose_phone(last_known, selected)
        if desired != selected:
            if process:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                process = None
            CAP.clear('origem desligada/trocada')
            selected = desired
            pending = b''
            capture_failures = 0
            pcm_silence_start = None
            pcm_silence_cleared = False
            next_capture_try = 0.0
            next_pcm_check = 0.0
            if selected:
                CAP.new_phone(selected)
            else:
                log(CAPTURE_LOG, 'Sem telemovel autorizado conectado; USB devolve silencio')
        if not selected:
            time.sleep(1)
            continue
        if process is None:
            # Do not start arecord every second while BlueALSA has not yet
            # published the PCM object (a common delay after reconnection).
            if now < next_capture_try or now < next_pcm_check:
                time.sleep(0.5)
                continue
            next_pcm_check = now + 3
            if not pcm_ready(selected):
                time.sleep(1)
                continue
            command = ['runuser', '-u', CAPTURE_USER, '--', 'arecord', '-q',
                       '-D', f'bluealsa:DEV={selected},PROFILE=a2dp',
                       '-t', 'raw', '-f', 'S16_LE', '-c', '2', '-r', str(RATE)]
            try:
                with CAPTURE_LOG.open('ab', buffering=0) as err:
                    process = subprocess.Popen(command, stdout=subprocess.PIPE,
                                               stderr=err, stdin=subprocess.DEVNULL,
                                               bufsize=0)
            except OSError as e:
                log(CAPTURE_LOG, f'Erro a iniciar arecord: {e}')
                CAP.clear('captura nao iniciou')
                capture_failures += 1
                next_capture_try = time.monotonic() + min(20, 2 ** min(4, capture_failures))
                time.sleep(1)
                continue
            log(CAPTURE_LOG, f'A2DP arecord iniciado para {selected}, pid={process.pid} boot={time.monotonic():.1f}s')
            FAST_CAPTURE_STARTED.set()
            last_packet = time.monotonic()

        if process.poll() is not None:
            log(CAPTURE_LOG, f'arecord terminou rc={process.returncode}')
            CAP.clear('captura terminou')
            process = None
            capture_failures += 1
            backoff = min(20, 2 ** min(4, capture_failures))
            log(CAPTURE_LOG, f'Captura falhou; nova tentativa em {backoff}s')
            next_capture_try = time.monotonic() + backoff
            time.sleep(1)
            continue
        ready, _, _ = select.select([process.stdout], [], [], 1.0)
        if ready:
            packet = os.read(process.stdout.fileno(), 8192)
            if not packet:
                CAP.clear('fim do fluxo Bluetooth')
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                process = None
                time.sleep(1)
                continue
            pending += packet
            aligned = len(pending) // FRAME_BYTES * FRAME_BYTES
            if aligned:
                chunk = pending[:aligned]
                pending = pending[aligned:]
                last_packet = time.monotonic()
                capture_failures = 0
                # A2DP may continue delivering *digital-zero* PCM while the
                # phone is paused. Clear those stale ring samples after 4s.
                # Near-silence with non-zero PCM isn't classified as silence.
                if not chunk.strip(b'\x00'):
                    if pcm_silence_start is None:
                        pcm_silence_start = last_packet
                    if last_packet - pcm_silence_start >= 4:
                        if not pcm_silence_cleared:
                            CAP.clear('4 segundos de PCM digitalmente silencioso')
                            pcm_silence_cleared = True
                    else:
                        CAP.add(chunk)
                else:
                    pcm_silence_start = None
                    pcm_silence_cleared = False
                    CAP.add(chunk)
        if time.monotonic() - last_packet >= 4:
            # No new PCM: zero every RAM sample and invalidate the WAV mapping.
            CAP.clear('4 segundos sem novos dados A2DP')
        # Next outer iteration probes Bluetooth, including newly paired phones.


# All USB positions are mapped onto one monotonic audio timeline:
# FLX00001.WAV => 0..30min; FLX00002.WAV => 30..60min; etc.
# No audio data are written to the image. Early host reads can cache silence.
SYNC_LOCK = threading.Lock()
ORIGIN_VIRTUAL = None
ORIGIN_SOURCE = None
ANCHOR_GENERATION = None
PREVIOUS_POS = None
PREVIOUS_FILE = None
FIRST_READ = None
LAST_LOG = 0.0
LAST_WARNING = 0.0


def after_fork():
    threading.Thread(target=capture_manager, name='BT-MultiPhone', daemon=True).start()
    log(CAPTURE_LOG, f'Bridge v0.5.6 iniciada, RAM limpa, FAT32 com {len(AUDIO_REGIONS)} WAV de 30min')


def open(readonly):
    return os.open(IMG, os.O_RDONLY)


def close(handle):
    os.close(handle)


def get_size(handle):
    return IMG.stat().st_size


def can_write(handle):
    return False


def pread(handle, buf, offset, flags):
    global ORIGIN_VIRTUAL, ORIGIN_SOURCE, ANCHOR_GENERATION
    global PREVIOUS_POS, PREVIOUS_FILE, FIRST_READ, LAST_LOG, LAST_WARNING
    n = len(buf)
    data = bytearray(os.pread(handle, n, offset))
    if len(data) != n:
        raise RuntimeError('Leitura curta da imagem FAT')
    now = time.monotonic()
    # Most NBD reads do not intersect PCM payload: FAT, root directory, headers.
    intersects = [(i, name, max(offset, start), min(offset + n, end), start)
                  for i, (name, start, end) in enumerate(AUDIO_REGIONS)
                  if offset < end and offset + n > start]
    if not intersects:
        buf[:] = data
        return
    with SYNC_LOCK:
        if FIRST_READ is None:
            FIRST_READ = now
            log(READ_LOG, '=== NOVA SESSAO USB v0.5.6 ===')
        with CAP.lock:
            generation = CAP.generation
            total = CAP.total
            receiving = CAP.active and now - CAP.last_rx < 4
            phone = CAP.phone
        if generation != ANCHOR_GENERATION:
            ORIGIN_VIRTUAL = ORIGIN_SOURCE = None
            ANCHOR_GENERATION = generation
            PREVIOUS_POS = None
            PREVIOUS_FILE = None
        for idx, name, a, b, file_start in intersects:
            if a >= b:
                continue
            virtual_pos = idx * VIRTUAL_TRACK_BYTES + (a - file_start)
            file_pos = (a - file_start) / BPS
            if name != PREVIOUS_FILE:
                log(READ_LOG, f'FILE_READ {name} pos={file_pos:.1f}s '
                              f'virtual={virtual_pos / BPS:.1f}s '
                              f'bt={total/BPS:.1f}s')
                PREVIOUS_FILE = name
            rewind = (PREVIOUS_POS is not None and
                      virtual_pos < PREVIOUS_POS - 12 * BPS)
            jump_ahead = (PREVIOUS_POS is not None and
                          virtual_pos > PREVIOUS_POS + 6 * BPS)
            if jump_ahead and now - LAST_WARNING > 3:
                log(READ_LOG, f'PREFETCH/SEEK salto={((virtual_pos-PREVIOUS_POS)/BPS):.1f}s '
                              f'ficheiro={name}; cache de silencio possivel')
                LAST_WARNING = now
            # After a long pause/seek the previous PCM position may have
            # fallen outside the 40s ring; re-anchor to live capture instead
            # of endlessly supplying silence. This cannot fix host caching.
            behind_ring = (ORIGIN_VIRTUAL is not None and
                           ORIGIN_SOURCE + (virtual_pos - ORIGIN_VIRTUAL) <
                           max(0, total - RING_SIZE) - 2 * BPS)
            if receiving and total >= PREFILL_BYTES and (
                    ORIGIN_VIRTUAL is None or rewind or behind_ring):
                ORIGIN_VIRTUAL = virtual_pos
                ORIGIN_SOURCE = max(0, total - PREFILL_BYTES)
                log(READ_LOG, f'RESYNC phone={phone} file={name} '
                              f'virtual={virtual_pos/BPS:.1f}s '
                              f'bt={ORIGIN_SOURCE/BPS:.1f}s '
                              f'buffer={PREFILL_SECONDS}s '
                              f'reason={"rewind" if rewind else "behind-ring" if behind_ring else "start"}')
            PREVIOUS_POS = virtual_pos
            copied, lag = 0, None
            if receiving and ORIGIN_VIRTUAL is not None:
                source_pos = ORIGIN_SOURCE + (virtual_pos - ORIGIN_VIRTUAL)
                if source_pos >= 0:
                    chunk, copied = CAP.get(source_pos, b - a)
                    data[a - offset:b - offset] = chunk
                    lag = total - source_pos
                else:
                    data[a - offset:b - offset] = bytes(b - a)
            else:
                data[a - offset:b - offset] = bytes(b - a)
            if now - LAST_LOG >= 2:
                nonzero = sum(byte != 0 for byte in data[a-offset:b-offset])
                lead = f'{lag / BPS:.1f}s' if lag is not None else 'n/a'
                log(READ_LOG, f't={now-FIRST_READ:.1f}s file={name} '
                              f'wav_pos={file_pos:.1f}s virtual={virtual_pos/BPS:.1f}s '
                              f'bt_received={total/BPS:.1f}s bt_connected={receiving} '
                              f'available={copied}/{b-a} nonzero={nonzero} lead={lead} '
                              f'phone={phone or "none"} generation={generation}')
                LAST_LOG = now
    buf[:] = data
