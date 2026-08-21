from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from match_extracted_sprite import ranked_matches  # noqa: E402


class SpriteMatcherTests(unittest.TestCase):
    def test_exact_visual_match_ranks_before_different_sprite(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            reference = directory / "reference.png"
            candidates = directory / "candidates"
            candidates.mkdir()
            exact = candidates / "exact.png"
            different = candidates / "different.png"
            Image.new("RGBA", (3, 5), (255, 0, 0, 255)).save(reference)
            Image.new("RGBA", (6, 10), (255, 0, 0, 255)).save(exact)
            Image.new("RGBA", (3, 5), (0, 0, 255, 255)).save(different)
            matches = ranked_matches(reference, candidates, 2)
            self.assertEqual(exact, matches[0][1])
            self.assertGreater(matches[1][0], matches[0][0])


if __name__ == "__main__":
    unittest.main()
