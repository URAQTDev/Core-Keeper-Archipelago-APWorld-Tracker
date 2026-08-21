from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PrototypeTargetAuditTests(unittest.TestCase):
    def test_every_candidate_is_classified_without_guessing(self) -> None:
        audit = json.loads(
            (ROOT / "data" / "prototype_check_target_audit.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            {"runtime_verified": 977, "verified_non_object_trigger": 120},
            audit["counts"],
        )
        self.assertEqual(1097, len(audit["records"]))

    def test_known_prototype_name_drift_resolves_to_runtime_objects(self) -> None:
        records = {record["check_name"]: record for record in json.loads(
            (ROOT / "data" / "prototype_check_target_audit.json").read_text(encoding="utf-8")
        )["records"]}
        self.assertEqual(9704, records["Collect Dagger Fish"]["object_id"])
        self.assertEqual(9740, records["Collect Litho Triolobite"]["object_id"])
        self.assertEqual(3190, records["Defeat S.A.H.A.B.A.R"]["object_id"])
        self.assertEqual(3149, records["Defeat Oblidra the Void Titan"]["object_id"])


if __name__ == "__main__":
    unittest.main()
