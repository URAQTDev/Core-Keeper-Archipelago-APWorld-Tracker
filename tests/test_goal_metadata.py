import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from build_goal_metadata import build  # noqa: E402


class GoalMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.actual = json.loads((ROOT / "data" / "goal_metadata.json").read_text())

    def test_metadata_matches_progression_graph(self):
        self.assertEqual(
            self.actual,
            build(ROOT / "data" / "goal_policy.json", ROOT / "data" / "progression_policy.json"),
        )

    def test_goal_order_default_and_required_counts(self):
        self.assertEqual("defeat_core_commander", self.actual["default_goal"])
        self.assertEqual(
            ["defeat_all_bosses", "defeat_sahabar", "defeat_core_commander", "lower_wall"],
            [goal["key"] for goal in self.actual["goals"]],
        )
        counts = {goal["key"]: goal["required_boss_checks"] for goal in self.actual["goals"]}
        self.assertEqual(
            {"lower_wall": 3, "defeat_core_commander": 10, "defeat_sahabar": 12, "defeat_all_bosses": 20},
            counts,
        )


if __name__ == "__main__":
    unittest.main()
