"""Passive detection of probable (not proven) user-initiated Blue&Me track changes.

Uses STATUS lines (actual sustained reads), never isolated FILE_READ or SEEK.
Prefetch, normal 30min boundary and very rapid repeated actions are rejected.
"""
from __future__ import annotations
from dataclasses import dataclass
import re

STATUS_RE = re.compile(
    r'\bt=(?P<t>[\d.]+)s\s+file=FLX(?P<track>\d{5})\.WAV\s+'
    r'wav_pos=(?P<pos>[\d.]+)s\b.*?'
    r'\bbt_connected=(?P<connected>True|False)\b.*?'
    r'\bnonzero=(?P<nonzero>\d+)\b.*?'
    r'\bgeneration=(?P<generation>\d+)\b'
)


@dataclass(frozen=True)
class Event:
    direction: str
    old: int
    new: int
    time_s: float
    confidence: str = 'PROBABLE_NOT_VERIFIED'


class Detector:
    def __init__(self):
        self.reset()

    def reset(self):
        self.active = None
        self.last = None
        self.stable_samples = 0
        self.candidate = None
        self.generation = None
        self.last_t = -1.0
        self.last_event_time = -1e6

    @staticmethod
    def parse(line):
        match = STATUS_RE.search(line)
        if not match:
            return None
        try:
            return (float(match['t']), int(match['track']), float(match['pos']),
                    match['connected'] == 'True' and int(match['nonzero']) > 0,
                    int(match['generation']))
        except (TypeError, ValueError, OverflowError):
            return None

    def process(self, line):
        parsed = self.parse(line)
        if not parsed:
            return None
        t, track, pos, audio, generation = parsed
        if not (0 <= t < 1e9 and 1 <= track <= 96 and 0 <= pos <= 1801):
            return None
        if generation != self.generation or t < self.last_t:
            self.reset()
            self.generation = generation
        self.last_t = t
        if not audio:
            self.candidate = None
            return None
        if self.active is None:
            if self.last and self.last[1] == track and 0.8 <= t - self.last[0] <= 12 and pos >= self.last[2] + .4:
                self.stable_samples += 1
            else:
                self.stable_samples = 1
            self.last = (t, track, pos)
            if self.stable_samples >= 3:
                self.active = track
            return None
        if track == self.active:
            self.last = (t, track, pos)
            self.stable_samples = min(10, self.stable_samples + 1)
            self.candidate = None
            return None
        # Old audio must be recently established and not near a natural 30min ending.
        if self.last is None or t - self.last[0] > 18 or self.last[2] > 1730:
            self.candidate = None
            return None
        delta = track - self.active
        if delta not in (-1, 1) or pos > 45 or t - self.last_event_time < 10:
            self.candidate = None
            return None
        if self.candidate is None or self.candidate[0] != track:
            self.candidate = (track, t, pos, 1)
            return None
        new, first_t, first_pos, seen = self.candidate
        if t - first_t > 12 or pos + .2 < first_pos:
            self.candidate = (track, t, pos, 1)
            return None
        seen += 1
        self.candidate = (new, first_t, first_pos, seen)
        if seen < 2 or t - first_t < 1.5 or pos - first_pos < .7:
            return None
        old = self.active
        self.active = new
        self.last = (t, track, pos)
        self.stable_samples = 2
        self.candidate = None
        self.last_event_time = t
        return Event('next' if delta == 1 else 'previous', old, new, t)
