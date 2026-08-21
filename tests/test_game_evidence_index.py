from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from build_game_evidence_index import build  # noqa: E402


class GameEvidenceIndexTests(unittest.TestCase):
    def test_checked_in_index_matches_extractor(self) -> None:
        checked_in = json.loads(
            (ROOT / "data" / "game_evidence_index.json").read_text(encoding="utf-8")
        )
        self.assertEqual(checked_in, build(ROOT / "data" / "game_config.raw.json"))

    def test_index_is_pinned_and_references_real_sources(self) -> None:
        index = json.loads(
            (ROOT / "data" / "game_evidence_index.json").read_text(encoding="utf-8")
        )
        manifest = json.loads(
            (ROOT / "data" / "source_manifest.json").read_text(encoding="utf-8-sig")
        )
        self.assertEqual(
            manifest["core_keeper"]["steam_build_id"],
            index["core_keeper_steam_build_id"],
        )
        by_id = {record["object_id"]: record["references"] for record in index["objects"]}
        self.assertTrue(any(index["sources"][ref[0]]["section"] == "loot" for ref in by_id[2021]))
        self.assertTrue(any(index["sources"][ref[0]]["section"] == "spawns" for ref in by_id[3009]))
        for refs in by_id.values():
            for ref in refs:
                source = index["sources"][ref[0]]
                self.assertEqual(64, len(source["sha256"]))
                expected_prefix = {"loot": "Loot/", "spawns": "Spawn/", "fishing": "Fishing/"}
                self.assertTrue(source["source"].startswith(expected_prefix[source["section"]]))

    def test_direct_fishing_results_are_indexed(self) -> None:
        index = json.loads(
            (ROOT / "data" / "game_evidence_index.json").read_text(encoding="utf-8")
        )
        fishing_sources = {
            source["source"] for source in index["sources"] if source["section"] == "fishing"
        }
        self.assertEqual(44, len(fishing_sources))
        indexed_fishing_sources = set()
        for obj in index["objects"]:
            for source_index, json_path, _container in obj["references"]:
                source = index["sources"][source_index]
                if source["section"] == "fishing" and json_path == "$.fish":
                    indexed_fishing_sources.add(source["source"])
        self.assertEqual(fishing_sources, indexed_fishing_sources)


if __name__ == "__main__":
    unittest.main()
