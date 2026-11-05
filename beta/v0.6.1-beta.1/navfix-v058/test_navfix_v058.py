#!/usr/bin/env python3
"""Offline integration checks for WAV jumps; no Bluetooth or USB required."""
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest

BASE = Path(__file__).resolve().parent
PATCHED = BASE / 'live_bt_nbd_v056_navfix058.py'
ORIGINAL_SHA = 'b4e1bae33ac9f018048e759573b86bed679b327e5d30a93f542c8a11e0f91f34'


class TestNavFix(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        os.environ['BM_LOG_DIR'] = self.tmp.name
        fake = types.ModuleType('fat_image_v050')
        fake.TRACK_SECONDS = 1800
        fake.image_regions = lambda path: []
        old_fake = sys.modules.get('fat_image_v050')
        sys.modules['fat_image_v050'] = fake
        self.addCleanup(self._restore, old_fake)
        spec = importlib.util.spec_from_file_location('navfix_test_plugin', PATCHED)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.mod = mod
        self.file = Path(self.tmp.name) / 'fake.img'
        # Three virtual PCM regions with realistic byte offsets.
        self.starts = [1024, 13_001_024, 26_001_024]
        with self.file.open('wb') as image:
            image.truncate(40_000_000)
        self.mod.IMG = self.file
        self.mod.AUDIO_REGIONS = [(f'FLX{i+1:05d}.WAV', start, start + 12_500_000)
                                  for i, start in enumerate(self.starts)]
        self.mod.CAP.add(b'\x21\x31\x41\x51' * (self.mod.RATE * 12))

    @staticmethod
    def _restore(old_fake):
        if old_fake is None:
            sys.modules.pop('fat_image_v050', None)
        else:
            sys.modules['fat_image_v050'] = old_fake

    def read(self, track, seconds=0, length=4096):
        offset = self.starts[track] + int(seconds * self.mod.BPS)
        out = bytearray(length)
        with self.file.open('rb') as fd:
            self.mod.pread(fd.fileno(), out, offset, 0)
        return bytes(out)

    def test_primary_track_audio_unchanged(self):
        self.assertTrue(any(self.read(0)))
        self.assertEqual(self.mod.PRIMARY_TRACK, 0)
        a = self.mod.ORIGIN_VIRTUAL, self.mod.ORIGIN_SOURCE
        self.read(0, 1)
        self.assertEqual((self.mod.ORIGIN_VIRTUAL, self.mod.ORIGIN_SOURCE), a)

    def test_next_track_no_long_silence(self):
        self.assertTrue(any(self.read(0)))
        self.assertTrue(any(self.read(1, 0)))
        self.assertEqual(self.mod.PRIMARY_TRACK, 0)
        self.assertIn(1, self.mod.SECONDARY_ANCHORS)

    def test_read_ahead_does_not_shift_primary(self):
        self.read(0)
        original_anchor = self.mod.ORIGIN_SOURCE
        self.read(2, 4)
        self.read(1, 5)
        self.assertEqual(self.mod.ORIGIN_SOURCE, original_anchor)
        self.assertTrue(any(self.read(0, 2)))

    def test_repeated_secondary_reads_continue(self):
        self.read(0)
        self.read(1)
        initial_anchor = self.mod.SECONDARY_ANCHORS[1][:2]
        self.assertTrue(any(self.read(1, 2)))
        self.assertEqual(self.mod.SECONDARY_ANCHORS[1][:2], initial_anchor)

    def test_ahead_seek_is_reanchored(self):
        self.read(0)
        self.read(1)
        self.assertTrue(any(self.read(1, 45)))
        self.assertEqual(self.mod.SECONDARY_ANCHORS[1][0], 45 * self.mod.BPS)

    def test_backward_navigation_to_primary_still_works(self):
        self.assertTrue(any(self.read(0)))
        self.assertTrue(any(self.read(1)))
        self.assertTrue(any(self.read(0)))

    def test_generation_change_clears_anchors(self):
        self.read(0)
        self.read(1)
        self.mod.CAP.clear('teste')
        self.mod.CAP.add(b'\x11\x22\x33\x44' * (self.mod.RATE * 10))
        self.assertTrue(any(self.read(2)))
        self.assertEqual(self.mod.PRIMARY_TRACK, 2)
        self.assertEqual(self.mod.SECONDARY_ANCHORS, {})

    def test_metadata_read_is_unchanged(self):
        out = bytearray(256)
        with self.file.open('rb') as fd:
            self.mod.pread(fd.fileno(), out, 0, 0)
        self.assertEqual(out, bytearray(256))
        self.assertIsNone(self.mod.PRIMARY_TRACK)


if __name__ == '__main__':
    unittest.main(verbosity=2)
