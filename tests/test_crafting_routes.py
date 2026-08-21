import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from build_crafting_routes import build  # noqa: E402


class CraftingRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paths = [
            ROOT / "data" / "check_candidates.json",
            ROOT / "data" / "runtime_database.raw.json",
            ROOT / "data" / "license_policy.json",
        ]
        cls.actual = json.loads((ROOT / "data" / "crafting_routes.json").read_text())
        cls.by_id = {entry["object_id"]: entry for entry in cls.actual["objects"]}

    def test_checked_in_routes_match_builder(self):
        self.assertEqual(self.actual, build(*self.paths))

    def test_bar_and_material_routes_use_exact_station_tiers(self):
        # Object IDs are verified in the runtime database; these assertions
        # guard the unusual stations explicitly called out in the design.
        expected = {
            1001: ("Progressive Furnace License", 1),  # Copper Bar
            1004: ("Progressive Furnace License", 2),  # Scarlet Bar
            1006: ("Progressive Furnace License", 2),  # Octarine Bar
            1008: ("Progressive Furnace License", 3),  # Solarite Bar
            1030: ("Table Saw License", 1),             # Plank
            1025: ("Glass Smelter License", 1),         # Glass Piece
        }
        for object_id, requirement in expected.items():
            actual = {(station["license"], station["license_stage"]) for station in self.by_id[object_id]["stations"]}
            self.assertIn(requirement, actual)

    def test_craftable_routes_retain_recipe_ingredients(self):
        copper_bar = self.by_id[1001]
        self.assertTrue(copper_bar["is_craftable"])
        ingredient_ids = {
            ingredient["object_id"]
            for variant in copper_bar["ingredient_variants"]
            for ingredient in variant["ingredients"]
        }
        self.assertIn(1500, ingredient_ids)  # Copper Ore


if __name__ == "__main__":
    unittest.main()
