from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from generate_catalog_consumers import equipment_rewards  # noqa: E402


class RewardObjectAuditTests(unittest.TestCase):
    def test_all_physical_reward_candidates_are_runtime_objects(self) -> None:
        audit = json.loads((ROOT / "data" / "reward_object_audit.json").read_text())
        self.assertEqual({"runtime_verified": 555}, audit["counts"])
        self.assertEqual(555, len(audit["records"]))

    def test_known_name_drift_maps_to_current_objects(self) -> None:
        records = {record["display_name"]: record for record in json.loads(
            (ROOT / "data" / "reward_object_audit.json").read_text()
        )["records"]}
        self.assertEqual(9123, records["Shellzooka"]["object_id"])
        self.assertEqual(8405, records["Morpha's Bubble Backpack"]["object_id"])
        self.assertEqual(9135, records["Storm Bringer"]["object_id"])

    def test_equipment_rewards_derive_from_all_five_validated_check_groups(self) -> None:
        catalog = json.loads((ROOT / "data" / "canonical_catalog.json").read_text())
        rewards = equipment_rewards(catalog)
        counts = {}
        for reward in rewards:
            counts[reward["option"]] = counts.get(reward["option"], 0) + 1
        self.assertEqual({
            "reward_tools": 41,
            "reward_weapons": 75,
            "reward_jewelry": 97,
            "reward_accessories": 59,
            "reward_armor": 188,
        }, counts)
        audited = {record["internal_name"] for record in catalog["objects"]}
        self.assertFalse([
            reward for reward in rewards
            if reward["internal_name"] not in audited
        ])


if __name__ == "__main__":
    unittest.main()
