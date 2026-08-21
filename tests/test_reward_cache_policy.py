import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RewardCachePolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = json.loads(
            (ROOT / "data" / "reward_cache_policy.json").read_text(encoding="utf-8")
        )
        cls.database = json.loads(
            (ROOT / "data" / "runtime_database.raw.json").read_text(encoding="utf-8")
        )
        cls.catalog = json.loads(
            (ROOT / "data" / "canonical_catalog.json").read_text(encoding="utf-8")
        )

    def test_cache_objects_are_exact_current_game_objects(self) -> None:
        runtime_names = {
            record["internal_name"]
            for record in self.database["records"]
            if record["variation"] == 0
        }
        for cache in self.policy["caches"]:
            with self.subTest(cache=cache["key"]):
                names = (
                    cache["objects"]
                    if "objects" in cache
                    else [choice["object"] for choice in cache["choices"]]
                )
                self.assertFalse(set(names) - runtime_names)
                if "objects" in cache:
                    self.assertEqual(len(names), len(set(names)))

    def test_amounts_select_one_stack_inclusive_of_requested_bounds(self) -> None:
        ranges = {
            cache["key"]: (cache["minimum_amount"], cache["maximum_amount"])
            for cache in self.policy["caches"]
            if "minimum_amount" in cache
        }
        self.assertEqual((5, 10), ranges["raw_material_cache"])
        self.assertEqual((5, 10), ranges["refined_material_cache"])
        self.assertEqual((3, 5), ranges["potions_cache"])
        self.assertEqual((1, 3), ranges["pet_cache"])
        self.assertEqual((50, 1000), ranges["money_cache"])
        self.assertEqual(50, next(
            cache["amount_step"] for cache in self.policy["caches"]
            if cache["key"] == "money_cache"
        ))

    def test_every_cache_policy_has_a_catalog_reward(self) -> None:
        rewards = {reward["display_name"] for reward in self.catalog["rewards"]}
        self.assertFalse(
            {cache["item_name"] for cache in self.policy["caches"]} - rewards
        )


if __name__ == "__main__":
    unittest.main()
