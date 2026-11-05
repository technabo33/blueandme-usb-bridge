import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'wheel'))
from detector import Detector


def s(t, track, pos, connected=True, nonzero=3500, generation=1):
    return (f'2026-11-05 15:21:21 t={t:.1f}s file=FLX{track:05d}.WAV '
            f'wav_pos={pos:.1f}s virtual=0s bt_received=90.2s '
            f'bt_connected={connected} available=4096/4096 '
            f'nonzero={nonzero} lead=8.0s '
            f'phone=AA:BB:CC:DD:EE:FF generation={generation}')


def base(d):
    for t,p in [(2,12),(5,15),(8,18),(11,21)]:
        assert d.process(s(t,1,p)) is None

class TestDetector(unittest.TestCase):
    def test_parse_never_exposes_mac(self):
        d=Detector()
        parsed=d.parse(s(5,1,20))
        self.assertEqual(parsed,(5.0,1,20.0,True,1))

    def test_real_next(self):
        d=Detector();base(d)
        self.assertIsNone(d.process(s(14,2,0)))
        ev=d.process(s(17,2,3))
        self.assertEqual((ev.direction,ev.old,ev.new),('next',1,2))

    def test_real_previous(self):
        d=Detector();base(d)
        d.process(s(14,2,0));d.process(s(17,2,3));d.process(s(20,2,6))
        self.assertIsNone(d.process(s(28,1,0)))
        ev=d.process(s(31,1,3))
        self.assertEqual((ev.direction,ev.old,ev.new),('previous',2,1))

    def test_prefetch_does_not_trigger(self):
        d=Detector();base(d)
        self.assertIsNone(d.process('FILE_READ FLX00002.WAV pos=0.0s virtual=1800.0s bt=4.1s'))
        self.assertIsNone(d.process(s(12,2,0)))
        self.assertIsNone(d.process(s(14,1,24)))
        self.assertIsNone(d.process(s(17,1,27)))
        self.assertIsNone(d.process(s(19,2,0)))
        self.assertIsNone(d.process(s(22,1,32)))

    def test_natural_track_boundary_not_skip(self):
        d=Detector()
        for t,p in [(2,1740),(5,1744),(8,1747),(11,1750)]: d.process(s(t,1,p))
        d.process(s(14,2,0))
        self.assertIsNone(d.process(s(17,2,3)))

    def test_silent_audio_never_triggers(self):
        d=Detector();base(d)
        d.process(s(14,2,0,nonzero=0))
        self.assertIsNone(d.process(s(17,2,3,nonzero=0)))

    def test_disconnected_audio_never_triggers(self):
        d=Detector();base(d)
        d.process(s(14,2,0,connected=False))
        self.assertIsNone(d.process(s(17,2,3,connected=False)))

    def test_requires_pos_progress(self):
        d=Detector();base(d)
        d.process(s(14,2,0))
        self.assertIsNone(d.process(s(17,2,0.2)))

    def test_reject_large_jumps(self):
        d=Detector();base(d)
        d.process(s(14,3,0))
        self.assertIsNone(d.process(s(17,3,3)))

    def test_cooldown(self):
        d=Detector();base(d)
        d.process(s(14,2,0));d.process(s(17,2,3))
        d.process(s(20,2,6))
        d.process(s(23,1,0))
        self.assertIsNone(d.process(s(25,1,2)))

    def test_generation_changes_reset(self):
        d=Detector();base(d)
        d.process(s(14,2,0))
        self.assertIsNone(d.process(s(17,2,3,generation=2)))

    def test_timestamps_rewind_reset(self):
        d=Detector();base(d)
        d.process(s(14,2,0))
        self.assertIsNone(d.process(s(4,2,3)))

    def test_reject_old_position_too_old(self):
        d=Detector();base(d)
        d.process(s(32,2,0))
        self.assertIsNone(d.process(s(35,2,3)))

    def test_invalid_parse(self):
        self.assertIsNone(Detector.parse('bad log with phone 00:00:00:00:00:00'))

if __name__=='__main__':unittest.main()
