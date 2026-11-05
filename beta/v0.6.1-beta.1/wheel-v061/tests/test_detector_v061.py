"""Synthetic and user-log-derived regression tests; no Bluetooth required."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from detector import Detector


def status(t, track, pos, generation=1, audio=True):
    return (f't={t:.1f}s file=FLX{track:05d}.WAV wav_pos={pos:.1f}s '
            f'virtual=0s bt_received=90.2s bt_connected={str(audio)} '
            f'available=4096/4096 nonzero={3500 if audio else 0} '
            f'lead=8.0s generation={generation}')


def feed(detector, samples):
    events = []
    for sample in samples:
        event = detector.process(status(*sample))
        if event:
            events.append((event.direction, event.old, event.new))
    return events


class TestWheel061(unittest.TestCase):
    def test_real_windows_log_next_after_two_original_samples(self):
        d = Detector()
        # From diagnostic v060b, generation 3, source only 2 samples.
        self.assertEqual(feed(d, [(1056.1, 1, 47.6, 3), (1058.8, 1, 49.0, 3),
                                  (1081.2, 2, 25.3, 3), (1084.2, 2, 28.2, 3),
                                  (1087.2, 2, 31.2, 3), (1089.9, 2, 34.2, 3)]),
                         [('next', 1, 2)])

    def test_wav10_to_9_is_previous(self):
        self.assertEqual(feed(Detector(), [(10,10,410),(13,10,413),
                                           (16,9,0),(19,9,3),(22,9,6)]),
                         [('previous', 10, 9)])

    def test_wav10_to_11_is_next(self):
        self.assertEqual(feed(Detector(), [(10,10,410),(13,10,413),
                                           (16,11,0),(19,11,3),(22,11,6)]),
                         [('next', 10, 11)])

    def test_prev_from_end_can_be_previous(self):
        self.assertEqual(feed(Detector(), [(10,10,1793),(13,10,1796),
                                           (16,9,17),(19,9,20),(22,9,23)]),
                         [('previous', 10, 9)])

    def test_previous_from_middle_previous_track(self):
        self.assertEqual(feed(Detector(), [(10,10,50),(13,10,53),
                                           (16,9,510),(19,9,513),(22,9,516)]),
                         [('previous', 10, 9)])

    def test_next_near_end_not_sent(self):
        self.assertEqual(feed(Detector(), [(10,10,1751),(13,10,1754),
                                           (16,11,0),(19,11,3),(22,11,6)]), [])

    def test_prefetch_one_status_not_sent(self):
        self.assertEqual(feed(Detector(), [(10,1,5),(13,1,8),(16,2,0),
                                           (19,1,14),(22,1,17)]), [])

    def test_reads_of_all_48_do_not_trigger(self):
        d=Detector()
        self.assertEqual(feed(d, [(10,1,5),(13,1,8)]), [])
        for n in range(2, 49):
            self.assertIsNone(d.process(f't=20s FILE_READ FLX{n:05d}.WAV pos=0.0s'))
            self.assertIsNone(d.process(f't=20s NAVFIX058 faixa=FLX{n:05d}.WAV motivo=new-wav'))
        self.assertEqual(feed(d, [(19,1,14),(22,1,17)]), [])

    def test_sequential_two_samples_destination_dont_trigger(self):
        self.assertEqual(feed(Detector(), [(10,1,5),(13,1,8),(16,2,0),(19,2,3)]), [])

    def test_nonadjacent_jump_baselines_without_event(self):
        self.assertEqual(feed(Detector(), [(10,1,5),(13,1,8),
                                           (16,38,0),(19,38,3),(22,38,6),
                                           (40,39,0),(43,39,3),(46,39,6)]),
                         [('next',38,39)])

    def test_next_and_previous_twice(self):
        self.assertEqual(feed(Detector(), [(10,1,5),(13,1,8),
                                           (16,2,0),(19,2,3),(22,2,6),
                                           (35,1,0),(38,1,3),(41,1,6),
                                           (55,2,0),(58,2,3),(61,2,6),
                                           (75,1,0),(78,1,3),(81,1,6)]),
                         [('next',1,2),('previous',2,1),('next',1,2),('previous',2,1)])

    def test_no_duplicate_on_same_track(self):
        self.assertEqual(feed(Detector(), [(10,1,5),(13,1,8),
                                           (16,2,0),(19,2,3),(22,2,6),
                                           (25,2,9),(28,2,12),(31,2,15)]),
                         [('next',1,2)])

    def test_manual_next_with_no_source_baseline_is_not_sent(self):
        self.assertEqual(feed(Detector(), [(10,1,5),(13,2,0),(16,2,3),(19,2,6)]), [])

    def test_audio_off_clears_baseline(self):
        self.assertEqual(feed(Detector(), [(10,1,5),(13,1,8),
                                           (16,1,11,1,False),
                                           (19,2,0),(22,2,3),(25,2,6)]), [])

    def test_generation_change_clears_baseline(self):
        self.assertEqual(feed(Detector(), [(10,1,5),(13,1,8),
                                           (16,2,0,2),(19,2,3,2),(22,2,6,2)]), [])

    def test_reject_fast_near_immediate_double_skip(self):
        self.assertEqual(feed(Detector(), [(10,1,5),(13,1,8),
                                           (16,2,0),(19,2,3),(22,2,6),
                                           (24,1,0),(26,1,3),(28,1,6)]),
                         [('next',1,2)])

    def test_reject_seek_nonprogressing(self):
        self.assertEqual(feed(Detector(), [(10,1,5),(13,1,8),
                                           (16,2,0),(19,2,0),(22,2,0)]), [])

    def test_forward_into_middle_seek_ignored(self):
        self.assertEqual(feed(Detector(), [(10,1,5),(13,1,8),
                                           (16,2,150),(19,2,153),(22,2,156)]), [])

    def test_previous_not_sent_for_nonadjacent_jump(self):
        self.assertEqual(feed(Detector(), [(10,10,5),(13,10,8),
                                           (16,7,0),(19,7,3),(22,7,6)]), [])

    def test_stale_source_over_180_seconds_not_sent(self):
        self.assertEqual(feed(Detector(), [(10,1,5),(13,1,8),
                                           (200,2,0),(203,2,3),(206,2,6)]), [])


if __name__ == '__main__':
    unittest.main()
