from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from build_acquisition_evidence import build  # noqa: E402


class AcquisitionEvidenceTests(unittest.TestCase):
    def test_checked_in_evidence_matches_builder(self) -> None:
        expected = build(
            ROOT / "data" / "check_candidates.json",
            ROOT / "data" / "runtime_database.raw.json",
            ROOT / "data" / "game_evidence_index.json",
        )
        actual = json.loads((ROOT / "data" / "acquisition_evidence.json").read_text())
        self.assertEqual(expected, actual)

    def test_every_object_check_has_runtime_evidence_record(self) -> None:
        candidates = json.loads((ROOT / "data" / "check_candidates.json").read_text())
        expected = {
            check["trigger"]["object_id"]
            for check in candidates["checks"]
            if "object_id" in check["trigger"]
        }
        evidence = json.loads((ROOT / "data" / "acquisition_evidence.json").read_text())
        actual = {record["object_id"] for record in evidence["objects"]}
        self.assertEqual(expected, actual)

    def test_copper_bar_recipe_is_grounded_in_game_station_data(self) -> None:
        evidence = json.loads((ROOT / "data" / "acquisition_evidence.json").read_text())
        by_id = {record["object_id"]: record for record in evidence["objects"]}
        copper_bar = by_id[1001]
        self.assertEqual([{"object_id": 1500, "amount": 1}], copper_bar["variations"][0]["ingredients"])
        self.assertTrue(copper_bar["crafting_stations"])


if __name__ == "__main__":
    unittest.main()
