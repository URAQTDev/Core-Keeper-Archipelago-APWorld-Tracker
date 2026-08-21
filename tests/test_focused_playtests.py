from __future__ import annotations

import re
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FOCUSED = ROOT / "playtest" / "focused"
GROUPS = (
    "critters",
    "goldensanity",
    "cardsanity",
    "blocksanity",
    "fishsanity",
    "skillsanity",
    "figurinesanity",
    "valuablesanity",
    "toolsanity",
    "weaponsanity",
    "accessanity",
    "jewelrysanity",
    "armorsanity",
    "petsanity",
    "merchantsanity",
)


class FocusedPlaytestTests(unittest.TestCase):
    def test_every_remaining_optional_group_has_one_focused_lower_wall_file(self):
        self.assertEqual(
            {f"{group}.yaml" for group in GROUPS},
            {path.name for path in FOCUSED.glob("*.yaml")},
        )
        for group in GROUPS:
            text = (FOCUSED / f"{group}.yaml").read_text(encoding="utf-8")
            self.assertIn("goal: lower_wall", text)
            enabled = re.findall(r"((?:[a-z_]+sanity)|critters): true", text)
            self.assertEqual([group], enabled)

    def test_room_manifest_matches_the_focused_matrix(self):
        manifest = json.loads((ROOT / "playtest" / "focused_rooms.json").read_text())
        self.assertEqual("lower_wall", manifest["goal"])
        rooms = {row["group"]: row for row in manifest["rooms"]}
        self.assertEqual(set(GROUPS), set(rooms))
        for room in rooms.values():
            self.assertRegex(room["archive"], r"^AP_[0-9]{20}\.zip$")
            self.assertRegex(room["sha256"], r"^[0-9a-f]{64}$")
            self.assertGreater(room["check_count"], 0)

    def test_launcher_is_manifest_and_hash_guarded(self):
        launcher = (ROOT / "Start-FocusedPlaytest.ps1").read_text(encoding="utf-8")
        self.assertIn("playtest\\focused_rooms.json", launcher)
        self.assertIn("Get-FileHash", launcher)
        self.assertIn("$actualHash -ne $record.sha256", launcher)
        self.assertIn("[switch]$ValidateOnly", launcher)
        self.assertIn("Start-Process -FilePath $ServerPath", launcher)
        for group in GROUPS:
            self.assertIn(f"'{group}'", launcher)


if __name__ == "__main__":
    unittest.main()
