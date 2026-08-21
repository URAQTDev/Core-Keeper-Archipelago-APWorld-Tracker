from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LicensePolicyTests(unittest.TestCase):
    def test_station_identities_are_exact_runtime_objects(self) -> None:
        policy = json.loads((ROOT / "data" / "license_policy.json").read_text())
        runtime = json.loads((ROOT / "data" / "runtime_database.raw.json").read_text())
        runtime_keys = {
            (record["object_id"], record["internal_name"], record["variation"])
            for record in runtime["records"]
        }
        stations = policy["stations"]
        self.assertEqual(len(stations), len({station["object_id"] for station in stations}))
        for station in stations:
            self.assertIn((station["object_id"], station["internal_name"], 0), runtime_keys)

    def test_progressive_stage_counts_match_actual_station_tiers(self) -> None:
        stations = json.loads((ROOT / "data" / "license_policy.json").read_text())["stations"]
        stages: dict[str, set[int]] = {}
        for station in stations:
            if station["license"]:
                stages.setdefault(station["license"], set()).add(station["stage"])
        self.assertEqual(set(range(1, 8)), stages["Progressive Workbench License"])
        self.assertEqual(set(range(1, 8)), stages["Progressive Anvil License"])
        self.assertEqual({1, 2, 3}, stages["Progressive Furnace License"])
        self.assertEqual({1, 2}, stages["Progressive Smithing Table License"])

    def test_basic_workbench_is_the_only_free_progressive_stage(self) -> None:
        stations = json.loads((ROOT / "data" / "license_policy.json").read_text())["stations"]
        free = [station for station in stations if station["stage"] == 0]
        self.assertEqual(["WoodenWorkBench"], [station["internal_name"] for station in free])
        self.assertIsNone(free[0]["license"])

    def test_station_groups_match_the_option_contract(self) -> None:
        stations = json.loads((ROOT / "data" / "license_policy.json").read_text())["stations"]
        by_license = {
            station["license"]: station["minimum_mode"]
            for station in stations
            if station["license"]
        }
        important = {
            "Progressive Furnace License",
            "Fishing Workbench License", "Egg Incubator License",
            "Key Casting Table License", "Salvage and Repair Station License",
            "Ancient Hologram Pod License", "Cooking Pot License", "Table Saw License",
        }
        for license_name in important:
            self.assertEqual("important_crafting", by_license[license_name])
        self.assertEqual("all", by_license["Pouch Workbench License"])
        self.assertEqual("all", by_license["Boat Workbench License"])
        options = (ROOT / "apworld" / "core_keeper" / "options.py").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            'class PouchWorkbenchLicense(LicenseToggle): display_name = "Pouch Workbench License"; default = 0',
            options,
        )
        self.assertLess(
            options.index('OptionGroup("Rewards (Licenses)"'),
            options.index('OptionGroup("Rewards (Items)"'),
        )

    def test_apworld_dataclass_emits_licenses_in_tracker_order(self) -> None:
        options = (ROOT / "apworld" / "core_keeper" / "options.py").read_text(
            encoding="utf-8"
        )
        dataclass_body = options.split("class CoreKeeperOptions", 1)[1].split(
            "option_groups =", 1
        )[0]
        expected = [
            "workbench_license", "anvil_license", "furnace_license",
            "repair_salvage_license", "cooking_pot_license", "hologram_license",
            "table_saw_license", "fishing_workbench_license", "egg_incubator_license",
            "key_casting_table_license", "alchemy_table_license",
            "jewelry_workbench_license", "automation_table_license",
            "smithing_table_license", "boat_workbench_license",
            "electronics_table_license", "pouch_workbench_license",
            "glass_smelter_license", "distillery_table_license", "rift_statue_license",
            "upgrade_station_license", "glass_workbench_license", "railway_forge_license",
            "loom_license", "go_kart_workbench_license", "carpenter_table_license",
            "livestock_workbench_license", "painter_table_license", "music_workbench_license",
        ]
        positions = [dataclass_body.index(f"    {option_name}:") for option_name in expected]
        self.assertEqual(sorted(positions), positions)


if __name__ == "__main__":
    unittest.main()
