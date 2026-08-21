from __future__ import annotations

import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
EXTRACTOR = ROOT / "tools" / "extract_game_config.py"
GAME_ROOT = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Core Keeper")


class DeterministicExtractTests(unittest.TestCase):
    @unittest.skipUnless(GAME_ROOT.exists(), "Core Keeper is not installed")
    def test_identical_inputs_produce_identical_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.json"
            second = Path(directory) / "second.json"
            command = [
                str(EXTRACTOR),
                str(GAME_ROOT),
                "placeholder",
                "--steam-build-id",
                "23543556",
            ]
            for output in (first, second):
                invocation = command.copy()
                invocation[2] = str(output)
                subprocess.run(
                    [__import__("sys").executable, *invocation],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            self.assertEqual(
                hashlib.sha256(first.read_bytes()).digest(),
                hashlib.sha256(second.read_bytes()).digest(),
            )


if __name__ == "__main__":
    unittest.main()
