import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from build_check_group_metadata import build  # noqa: E402


class CheckGroupMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.actual = json.loads((ROOT / "data" / "check_group_metadata.json").read_text())

    def test_metadata_matches_verified_inventory(self):
        expected = build(
            ROOT / "data" / "check_group_policy.json",
            ROOT / "data" / "check_candidates.json",
        )
        self.assertEqual(expected, self.actual)
        self.assertEqual(1122, sum(group["check_count"] for group in self.actual["groups"]))

    def test_all_opt_in_check_groups_default_off(self):
        by_key = {group["key"]: group for group in self.actual["groups"]}
        opt_in = {
            "unique_materials", "key_items", "bosses", "merchantsanity", "petsanity", "fishsanity", "blocksanity",
            "goldensanity", "critters", "cattle_mutilation", "skillsanity",
            "figurinesanity", "cardsanity", "valuablesanity", "toolsanity",
            "weaponsanity", "jewelrysanity", "accessanity", "armorsanity",
        }
        for key in opt_in:
            self.assertFalse(by_key[key]["default_enabled"], key)

    def test_descriptions_have_counts_and_examples(self):
        for group in self.actual["groups"]:
            self.assertIn(str(group["check_count"]), group["description"])
            self.assertEqual(3, len(group["examples"]))

    def test_groups_follow_default_optional_sanity_taxonomy(self):
        self.assertEqual([
            "raw_materials", "refined_materials", "locked_chests", "seeds", "food", "enemies",
            "unique_materials", "key_items", "bosses", "merchantsanity", "petsanity",
            "blocksanity", "goldensanity", "critters", "cattle_mutilation",
            "skillsanity", "fishsanity", "figurinesanity", "cardsanity", "valuablesanity",
            "toolsanity", "weaponsanity", "jewelrysanity", "accessanity", "armorsanity",
        ], [group["key"] for group in self.actual["groups"]])
        by_key = {group["key"]: group for group in self.actual["groups"]}
        self.assertEqual("Bosses", by_key["bosses"]["display_name"])
        self.assertEqual("Fishsanity", by_key["fishsanity"]["display_name"])


if __name__ == "__main__":
    unittest.main()
