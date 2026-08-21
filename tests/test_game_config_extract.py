from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "tools" / "extract_game_config.py"
SPEC = importlib.util.spec_from_file_location("extract_game_config", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ParseIdMapTests(unittest.TestCase):
    def test_parses_game_comma_less_format(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ObjectID.json"
            path.write_text('{\n"None": 0\n"CopperShovel": 1\n}\n', encoding="utf-8")
            self.assertEqual({"None": 0, "CopperShovel": 1}, MODULE.parse_id_map(path))

    def test_rejects_duplicate_ids(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ObjectID.json"
            path.write_text('{\n"One": 1\n"Another": 1\n}\n', encoding="utf-8")
            with self.assertRaises(ValueError):
                MODULE.parse_id_map(path)

    def test_rejects_duplicate_names(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ObjectID.json"
            path.write_text('{\n"One": 1\n"One": 2\n}\n', encoding="utf-8")
            with self.assertRaises(ValueError):
                MODULE.parse_id_map(path)


if __name__ == "__main__":
    unittest.main()
