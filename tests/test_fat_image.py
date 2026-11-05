import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from fat_image_v050 import create_image, image_regions, wav_header, playlist_data, TRACK_SIZE


class FATImageTest(unittest.TestCase):
    def test_wav_header(self):
        h = wav_header()
        self.assertEqual(len(h), 44)
        self.assertTrue(h.startswith(b'RIFF'))
        self.assertIn(b'WAVE', h)

    def test_two_tracks_sparse(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / 'example.img'
            create_image(image, 1)
            regions = image_regions(image)
            self.assertEqual(len(regions), 2)
            self.assertEqual([r[0] for r in regions], ['FLX00001.WAV', 'FLX00002.WAV'])
            self.assertEqual(regions[0][2] - regions[0][1], TRACK_SIZE - 44)
            self.assertLess(image.stat().st_blocks * 512, 15 * 1024 * 1024)
            with self.assertRaises(FileExistsError):
                create_image(image, 1)

    def test_out_of_range(self):
        with self.assertRaises(ValueError):
            create_image('/tmp/ignored-blueandme-test.img', 0)


if __name__ == '__main__':
    unittest.main()
