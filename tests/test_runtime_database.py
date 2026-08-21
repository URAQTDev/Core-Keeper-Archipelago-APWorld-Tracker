from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "import_runtime_database.py"
SPEC = importlib.util.spec_from_file_location("import_runtime_database", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RuntimeDatabaseTests(unittest.TestCase):
    def test_checked_in_database_is_valid_and_deterministic(self) -> None:
        source = ROOT / "data" / "runtime_database.raw.json"
        normalized = MODULE.normalize(
            source,
            ROOT / "data" / "game_config.raw.json",
            ROOT / "data" / "source_manifest.json",
        )
        checked_in = json.loads(source.read_text(encoding="utf-8"))
        self.assertEqual(2876, len(checked_in["records"]))
        self.assertEqual(checked_in["records"], normalized["records"])
        self.assertEqual([4600], checked_in["unresolved_internal_station_recipe_ids"])

    def test_rejects_unknown_ingredient(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = json.loads((ROOT / "data" / "runtime_database.raw.json").read_text())
            runtime["records"][0]["ingredients"] = [{"object_id": 999999999, "amount": 1}]
            path = Path(directory) / "runtime.json"
            path.write_text(json.dumps(runtime), encoding="utf-8")
            with self.assertRaises(ValueError):
                MODULE.normalize(
                    path,
                    ROOT / "data" / "game_config.raw.json",
                    ROOT / "data" / "source_manifest.json",
                )


if __name__ == "__main__":
    unittest.main()
