"""Conservative Next/Previous detector for Blue&Me WAV USB activity.

Patch only the v0.6.0 WheelControl sidecar: no changes to A2DP, USB or WAV.
Requires multiple progress samples in STATUS log; FILE_READ and NAVFIX alone
never trigger media actions. Observed playback is a heuristic, not direct button.
"""
from __future__ import annotations
from dataclasses import dataclass
import re

STATUS_RE = re.compile(
    r"\bt=(?P<t>[\d.]+)s\s+file=FLX(?P<track>\d{5})\.WAV\s+"
    r"wav_pos=(?P<pos>[\d.]+)s\b.*?"
    r"\bbt_connected=(?P<connected>True|False)\b.*?"
    r"\bnonzero=(?P<nonzero>\d+)\b.*?"
    r"\bgeneration=(?P<generation>\d+)\b"
)


@dataclass(frozen=True)
class Event:
    direction: str
    old: int
    new: int
    time_s: float
    confidence: str = 'PROBABLE_NOT_VERIFIED'


class Detector:
    """Recognize *probable* Next/Previous via 2 stable source + 3 destination STATUS.

    When generation changes, the previous baseline is discarded. Unstable or
    non-adjacent transitions merely re-establish the baseline, no action sent.
    """
    def __init__(self):
        self.reset()

    def reset(self):
        self.generation = None
        self.last_t = -1.0
        self.run = None  # (track, first_t, first_pos, last_t, last_pos, samples)
        self.active = None
        self.active_t = -1.0
        self.active_pos = 0.0
        self.last_event_time = -1e9

    @staticmethod
    def parse(line):
        m = STATUS_RE.search(line)
        if not m:
            return None
        try:
            return (float(m['t']), int(m['track']), float(m['pos']),
                    m['connected'] == 'True' and int(m['nonzero']) > 0,
                    int(m['generation']))
        except (TypeError, ValueError, OverflowError):
            return None

    def process(self, line):
        parsed = self.parse(line)
        if parsed is None:
            return None
        t, track, pos, audio, generation = parsed
        if not (0 <= t < 1e9 and 1 <= track <= 48 and 0 <= pos <= 1801):
            return None
        if self.generation != generation or t < self.last_t:
            self.reset()
            self.generation = generation
        self.last_t = t
        if not audio:
            self.active = None
            self.run = None
            return None

        if self.run is not None:
            rt, first_t, first_pos, last_t, last_pos, count = self.run
            dt = t - last_t
            dp = pos - last_pos
            if rt == track and 0.8 <= dt <= 12 and .3 <= dp <= 18:
                self.run = (track, first_t, first_pos, t, pos, count + 1)
            else:
                self.run = (track, t, pos, t, pos, 1)
        else:
            self.run = (track, t, pos, t, pos, 1)

        rt, first_t, first_pos, last_t, last_pos, count = self.run
        # At least two samples for baseline (observed Windows: precisely two).
        if self.active is None:
            if count >= 2 and t - first_t >= .8:
                self.active = track
                self.active_t = t
                self.active_pos = pos
            return None
        if track == self.active:
            # Refresh the current track only after corroborated progress.
            if count >= 2:
                self.active_t = t
                self.active_pos = pos
            return None
        # Another WAV must actually be progressing, not just prefetched.
        if count < 3 or t - first_t < 2.5:
            return None

        old = self.active
        previous_t = self.active_t
        previous_pos = self.active_pos
        # Re-baseline all sustained switches, even non-adjacent ones.
        self.active = track
        self.active_t = t
        self.active_pos = pos
        # Adjacent tracks only: other jumps can be random play or scanning.
        delta = track - old
        if delta not in (-1, 1):
            return None
        if not (0 <= first_t - previous_t <= 180
                and t - self.last_event_time >= 9):
            return None
        if delta == 1:
            # Next before the 30-min WAV ends. Leave an end-of-file margin
            # because natural transitions and caching are indistinguishable.
            if previous_pos >= 1750 or first_pos > 120:
                return None
        # Previous: a sustained return to the immediately preceding WAV.
        # Does not need the position/end-of-file restrictions from Next.
        self.last_event_time = t
        return Event('next' if delta == 1 else 'previous', old, track, t)
