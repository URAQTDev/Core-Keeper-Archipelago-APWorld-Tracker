from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CheckCandidateTests(unittest.TestCase):
    def test_inventory_is_complete_unique_and_not_prematurely_logical(self) -> None:
        data = json.loads(
            (ROOT / "data" / "check_candidates.json").read_text(encoding="utf-8")
        )
        checks = data["checks"]
        self.assertEqual(1122, len(checks))
        self.assertEqual(len(checks), len({check["stable_id"] for check in checks}))
        self.assertEqual(len(checks), len({check["display_name"] for check in checks}))
        self.assertTrue(all(check["normal_logic"] is None for check in checks))
        self.assertTrue(all(check["status"] == "target_verified_logic_pending" for check in checks))

    def test_known_display_name_drift_is_corrected(self) -> None:
        checks = {check["display_name"]: check for check in json.loads(
            (ROOT / "data" / "check_candidates.json").read_text(encoding="utf-8")
        )["checks"]}
        self.assertIn("Collect Shiny Larva Meat", checks)
        self.assertIn("Collect Dagger Fin", checks)
        self.assertIn("Collect Litho Trilobite", checks)
        self.assertNotIn("Collect Golden Larva Meat", checks)

    def test_trigger_kinds_match_check_semantics(self) -> None:
        checks = {check["display_name"]: check for check in json.loads(
            (ROOT / "data" / "check_candidates.json").read_text(encoding="utf-8")
        )["checks"]}
        self.assertEqual("natural_acquisition", checks["Collect Ancient Coin"]["trigger"]["kind"])
        self.assertEqual("kill", checks["Slay Shrooman"]["trigger"]["kind"])
        self.assertEqual("unlock", checks["Unlock Locked Copper Chest"]["trigger"]["kind"])
        self.assertEqual("hatch", checks["Hatch Subterrier"]["trigger"]["kind"])
        self.assertEqual("skill_level", checks["Level 10 Mining"]["trigger"]["kind"])


if __name__ == "__main__":
    unittest.main()
