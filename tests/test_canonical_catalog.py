from __future__ import annotations

import json
import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from generate_catalog_consumers import generate  # noqa: E402
from validate_catalog import validate, validate_semantics  # noqa: E402


class CanonicalCatalogTests(unittest.TestCase):
    def test_non_guaranteed_world_items_are_not_checks(self) -> None:
        catalog = json.loads((ROOT / "data" / "canonical_catalog.json").read_text(encoding="utf-8"))
        check_names = {record["display_name"] for record in catalog["checks"]}
        excluded = {
            "Collect Ammonite Necklace", "Collect Ancient Guardian Necklace",
            "Collect Caveling Mother's Ring", "Collect Conch Shell Necklace",
            "Collect Turtle Shell", "Collect Oceanheart Necklace",
            "Collect Spine Ring", "Collect Frozen Flame", "Collect White Whistle",
            "Collect Tower Shell Necklace",
        }
        self.assertTrue(excluded.isdisjoint(check_names))

    def test_catalog_matches_pinned_game_evidence(self) -> None:
        validate(
            ROOT / "data" / "canonical_catalog.json",
            ROOT / "data" / "game_config.raw.json",
            ROOT / "data" / "source_manifest.json",
            ROOT,
        )

    def test_slice_consumers_match_catalog(self) -> None:
        generate(ROOT, check=True)
        catalog = json.loads((ROOT / "data" / "canonical_catalog.json").read_text(encoding="utf-8"))
        locations = {
            record["display_name"]: record["stable_id"] for record in catalog["checks"]
        }
        items = {
            record["display_name"]: record["stable_id"] for record in catalog["rewards"]
        }
        location_source = (ROOT / "apworld" / "core_keeper" / "locations.py").read_text(encoding="utf-8")
        item_source = (ROOT / "apworld" / "core_keeper" / "items.py").read_text(encoding="utf-8")
        for name, stable_id in locations.items():
            self.assertIn(f'{json.dumps(name)}: {stable_id}', location_source)
        for name, stable_id in items.items():
            self.assertIn(f'{json.dumps(name)}: {stable_id}', item_source)

    def test_trigger_and_delivery_kinds_match_runtime_object_kinds(self) -> None:
        catalog = json.loads((ROOT / "data" / "canonical_catalog.json").read_text(encoding="utf-8"))
        validate_semantics(catalog)

        invalid_check = copy.deepcopy(catalog)
        invalid_check["checks"][0]["trigger"] = {
            "kind": "kill",
            "target_key": "wood",
        }
        with self.assertRaisesRegex(ValueError, "kill with item target wood"):
            validate_semantics(invalid_check)

        invalid_reward = copy.deepcopy(catalog)
        invalid_reward["rewards"][0]["delivery"] = {
            "kind": "license",
            "target_key": "wood",
            "amount": 1,
        }
        with self.assertRaisesRegex(ValueError, "license with item target wood"):
            validate_semantics(invalid_reward)


if __name__ == "__main__":
    unittest.main()
