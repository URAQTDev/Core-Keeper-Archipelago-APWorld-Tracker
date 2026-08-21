import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from build_game_reference_semantics import build  # noqa: E402


class GameReferenceSemanticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paths = [
            ROOT / "data" / "check_candidates.json",
            ROOT / "data" / "game_config.raw.json",
            ROOT / "data" / "game_evidence_index.json",
            ROOT / "data" / "game_enums.raw.json",
        ]
        cls.actual = json.loads((ROOT / "data" / "game_reference_semantics.json").read_text())

    def test_checked_in_semantics_match_builder(self):
        self.assertEqual(self.actual, build(*self.paths))

    def test_spawn_context_uses_current_game_enum_names(self):
        by_id = {entry["object_id"]: entry for entry in self.actual["objects"]}
        shrooman_spawns = [
            ref for ref in by_id[3009]["references"] if ref["section"] == "spawns"
        ]
        self.assertTrue(shrooman_spawns)
        self.assertTrue(any(ref["context"]["biome"]["name"] == "Slime" for ref in shrooman_spawns))
        self.assertTrue(any(
            any(tileset["name"] == "Turf" for tileset in ref["context"]["tilesets"])
            for ref in shrooman_spawns
        ))

    def test_all_direct_fish_definitions_survive_interpretation(self):
        direct_fish = {
            ref["source"]
            for entry in self.actual["objects"]
            for ref in entry["references"]
            if ref["context"].get("direct_fish_definition")
        }
        self.assertEqual(44, len(direct_fish))

    def test_every_numeric_acquisition_context_has_a_known_enum_name(self):
        for entry in self.actual["objects"]:
            for ref in entry["references"]:
                context = ref["context"]
                for field in ("biome", "biome_filter", "tile_type"):
                    value = context.get(field)
                    if value is not None:
                        self.assertIsNotNone(
                            value["name"],
                            f"unknown {field} value {value['value']} in {ref['source']}",
                        )
                for tileset in context.get("tilesets", []):
                    self.assertIsNotNone(
                        tileset["name"],
                        f"unknown tileset {tileset['value']} in {ref['source']}",
                    )


if __name__ == "__main__":
    unittest.main()
