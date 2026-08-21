from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class GameEnumTests(unittest.TestCase):
    def test_spawn_numeric_values_have_current_game_names(self) -> None:
        data = json.loads((ROOT / "data" / "game_enums.raw.json").read_text())
        self.assertEqual(8, data["enums"]["Biome"]["Desert"])
        self.assertEqual(10, data["enums"]["Biome"]["Passage"])
        self.assertEqual(11, data["enums"]["Biome"]["Excavation"])
        self.assertEqual(26, data["enums"]["Tileset"]["Desert"])
        self.assertEqual(46, data["enums"]["TileType"]["ground"])
        self.assertEqual(-1, data["enums"]["TileType"]["__illegal__"])


if __name__ == "__main__":
    unittest.main()
