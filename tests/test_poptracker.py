from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from build_poptracker import (  # noqa: E402
    CHECK_ORDER_OVERRIDES,
    IMPORTANT_LICENSES,
    LICENSES,
    OTHER_LICENSES,
    CHECK_CATEGORIES,
    SKILL_TABS,
    outputs,
)
from package_poptracker import build as package  # noqa: E402


class PopTrackerTests(unittest.TestCase):
    def test_logic_autotracking_uses_individual_enabled_licenses(self):
        source = (ROOT / "poptracker" / "scripts" / "logic_autotracking.lua").read_text(
            encoding="utf-8"
        )
        self.assertIn('slot_data["enabled_licenses"]', source)
        self.assertIn("CurrentEnabledLicenses[LicenseNames[code]]", source)
        self.assertNotIn("CurrentLicenseMode", source)

    def test_new_food_checks_have_requested_tracker_neighbors(self):
        food = CHECK_ORDER_OVERRIDES["food"]
        self.assertEqual(
            food.index("collect_dodo_egg") + 1,
            food.index("collect_paradise_fruit_basket"),
        )
        self.assertEqual(
            food.index("collect_pinegrapple") + 1,
            food.index("collect_splendid_amalgam"),
        )

    @staticmethod
    def centered_arrays(widget: dict) -> list[dict]:
        if widget["type"] == "array":
            return [widget]
        if widget["type"] == "tabbed":
            return [
                centered
                for tab in widget["tabs"]
                for centered in PopTrackerTests.centered_arrays(tab["content"])
            ]
        raise AssertionError(f"Unexpected tracker layout type: {widget['type']}")

    def test_layouts_preserve_prototype_stable_id_order_within_each_group(self):
        catalog = json.loads((ROOT / "data" / "canonical_catalog.json").read_text())
        order = json.loads((ROOT / "data" / "prototype_tracker_order.json").read_text())
        by_id = {check["stable_id"]: check for check in catalog["checks"]}
        expected = {}
        for stable_id in order["stable_ids"]:
            if stable_id not in by_id:
                continue
            check = by_id[stable_id]
            expected.setdefault(check["group"], []).append(check["key"])
        for stable_id in sorted(set(by_id) - set(order["stable_ids"])):
            check = by_id[stable_id]
            expected.setdefault(check["group"], []).append(check["key"])
        raw = expected["raw_materials"]
        raw.remove("collect_pandorium_ore")
        raw.insert(raw.index("collect_desert_ruby") + 1, "collect_pandorium_ore")
        expected.update(CHECK_ORDER_OVERRIDES)
        expected["skillsanity"] = [
            f"level_{level}_{suffix}"
            for _title, suffix in SKILL_TABS
            for level in range(10, 101, 10)
        ]

        layout = json.loads((ROOT / "poptracker" / "xl" / "layouts" / "tracker.json").read_text())
        tabs = layout["tracker_default"]["content"]["tabs"]
        metadata = json.loads((ROOT / "data" / "check_group_metadata.json").read_text())
        group_by_title = {group["display_name"]: group["key"] for group in metadata["groups"]}
        check_tabs = [tab for tab in tabs if tab["title"] != "Licenses"]
        expected_groups = [group for _, groups in CHECK_CATEGORIES for group in groups]
        expected_titles = {
            group["key"]: group["display_name"] for group in metadata["groups"]
        }
        self.assertEqual([expected_titles[group] for group in expected_groups], [tab["title"] for tab in check_tabs])
        for tab in check_tabs:
            actual = [
                code
                for page in self.centered_arrays(tab["content"])
                for row in page["content"][1]["rows"]
                for code in row
            ]
            self.assertEqual(expected[group_by_title[tab["title"]]], actual, tab["title"])

    @staticmethod
    def layout_codes(layout: dict) -> list[str]:
        codes = []
        for group in layout["content"]["tabs"]:
            if group["title"] == "Licenses":
                continue
            for centered in PopTrackerTests.centered_arrays(group["content"]):
                grid = centered["content"][1]
                codes.extend(code for row in grid["rows"] for code in row)
        return codes

    def test_manifest_uses_only_supported_targeted_fields(self):
        manifest = json.loads((ROOT / "poptracker" / "manifest.json").read_text())
        self.assertEqual("Core Keeper", manifest["game_name"])
        self.assertEqual("0.35.3", manifest["target_poptracker_version"])
        self.assertEqual(["medium", "small", "large", "xl"], list(manifest["variants"]))
        for variant in manifest["variants"].values():
            self.assertEqual(["ap"], variant["flags"])

    def test_generated_definitions_and_layouts_are_current(self):
        for path, expected in outputs(ROOT).items():
            self.assertEqual(expected, path.read_text(encoding="utf-8-sig"), path)

    def test_layouts_are_resizable_and_paginate_large_groups(self):
        for variant in ("medium", "small", "large", "xl"):
            layout = json.loads(
                (ROOT / "poptracker" / variant / "layouts" / "tracker.json").read_text()
            )["tracker_default"]
            self.assertEqual("dock", layout["type"])
            group_tabs = layout["content"]["tabs"]
            metadata = json.loads((ROOT / "data" / "check_group_metadata.json").read_text())
            titles = {group["key"]: group["display_name"] for group in metadata["groups"]}
            expected_titles = ["Licenses"] + [
                titles[group] for _, groups in CHECK_CATEGORIES for group in groups
            ]
            self.assertEqual(
                expected_titles,
                [tab["title"] for tab in group_tabs],
            )
            for group in group_tabs:
                contents = self.centered_arrays(group["content"])
                for centered in contents:
                    self.assertEqual("array", centered["type"])
                    self.assertEqual("horizontal", centered["orientation"])
                    self.assertEqual(["text", "itemgrid", "text"], [
                        child["type"] for child in centered["content"]
                    ])
                    page = centered["content"][1]
                    row_width = max(map(len, page["rows"]))
                    row_lengths = [len(row) for row in page["rows"]]
                    if group["title"] == "Skillsanity":
                        self.assertEqual(10, sum(row_lengths))
                        self.assertLessEqual(max(row_lengths) - min(row_lengths), 1)
                    else:
                        self.assertLessEqual(abs(len(page["rows"]) - row_width), 1)

    def test_every_variant_lays_out_every_check_exactly_once(self):
        catalog = json.loads((ROOT / "data" / "canonical_catalog.json").read_text())
        expected = [check["key"] for check in catalog["checks"]]
        self.assertEqual(1115, len(expected))
        for variant in ("medium", "small", "large", "xl"):
            layout = json.loads(
                (ROOT / "poptracker" / variant / "layouts" / "tracker.json").read_text()
            )["tracker_default"]
            actual = self.layout_codes(layout)
            self.assertEqual(len(expected), len(actual), variant)
            self.assertEqual(set(expected), set(actual), variant)

    def test_every_variant_has_all_license_controls(self):
        logic = json.loads((ROOT / "poptracker" / "items" / "logic.json").read_text())
        expected = {
            item["codes"] for item in logic
            if "license" in str(item.get("codes", ""))
        }
        self.assertEqual(29, len(expected))
        for variant in ("medium", "small", "large", "xl"):
            layout = json.loads(
                (ROOT / "poptracker" / variant / "layouts" / "tracker.json").read_text()
            )["tracker_default"]
            tab = next(tab for tab in layout["content"]["tabs"] if tab["title"] == "Licenses")
            grid = tab["content"]["content"][1]
            ordered = [code for row in grid["rows"] for code in row]
            self.assertEqual(IMPORTANT_LICENSES + OTHER_LICENSES, ordered, variant)
            self.assertEqual(LICENSES, ordered, variant)
            actual = set(ordered)
            self.assertEqual(expected, actual, variant)

    def test_asset_manifest_covers_every_catalog_check_and_state(self):
        catalog = json.loads((ROOT / "data" / "canonical_catalog.json").read_text())
        manifest = json.loads((ROOT / "data" / "tracker_asset_manifest.json").read_text())
        assets = {entry["check_key"]: entry for entry in manifest["assets"]}
        active = {check["key"] for check in catalog["checks"]}
        self.assertTrue(active.issubset(assets))
        for key in active:
            entry = assets[key]
            self.assertNotIn("wiki", entry["source"].casefold())
            for state in ("checked", "unchecked", "unavailable"):
                output = entry["outputs"][state]
                path = ROOT / "poptracker" / "images" / output["path"]
                self.assertTrue(path.is_file())
                self.assertEqual(output["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())

    def test_every_variant_has_visible_icons_for_every_check(self):
        catalog = json.loads((ROOT / "data" / "canonical_catalog.json").read_text())
        for variant in ("medium", "small", "large", "xl"):
            for check in catalog["checks"]:
                stable_id = check["stable_id"]
                for folder in ("check-icons", "check-icons-disabled", "check-icons-absent"):
                    path = ROOT / "poptracker" / variant / "images" / folder / f"{stable_id}.png"
                    self.assertTrue(path.is_file(), f"{variant}: {check['key']} {folder}")

    def test_texture_only_mappings_are_not_rendered_directly(self):
        manifest = {
            entry["check_key"]: entry
            for entry in json.loads((ROOT / "data" / "tracker_asset_manifest.json").read_text())["assets"]
        }
        self.assertTrue(manifest)
        texture_only = [
            key for key, entry in manifest.items()
            if entry["unity_object_type"] == "Texture2D"
        ]
        self.assertEqual(
            set(),
            set(texture_only),
        )

    def test_critters_use_exact_local_object_icons(self):
        catalog = json.loads((ROOT / "data" / "canonical_catalog.json").read_text())
        critters = {check["key"] for check in catalog["checks"] if check["group"] == "critters"}
        manifest = {
            entry["check_key"]: entry
            for entry in json.loads((ROOT / "data" / "tracker_asset_manifest.json").read_text())["assets"]
        }
        self.assertEqual(25, len(critters))
        for key in critters:
            self.assertEqual("ObjectInfo.icon", manifest[key]["unity_object_type"], key)
            self.assertEqual("verified_exact_local_game_object_icon", manifest[key]["usage_status"], key)
            self.assertTrue(manifest[key]["source"].startswith("local_game_object_icon/"), key)

    def test_corrected_groups_use_exact_local_game_sources(self):
        manifest = {
            entry["check_key"]: entry
            for entry in json.loads((ROOT / "data" / "tracker_asset_manifest.json").read_text())["assets"]
        }
        corrected = {
            "collect_white_hydra_eye", "collect_azeos_feather_fan",
            "collect_omoroth_compass", "collect_heart_berry_seed",
            "collect_amber_larva", "defeat_omoroth", "defeat_ra_akar",
            "defeat_nimruza", "defeat_sahabar", "defeat_hive_mother",
            "defeat_ivy", "defeat_morpha", "defeat_igneous",
            "defeat_atlantean_worm", "defeat_urschleim", "defeat_oblidra",
        }
        self.assertEqual(16, len(corrected))
        for key in corrected:
            self.assertEqual("ObjectInfo.icon", manifest[key]["unity_object_type"], key)
            self.assertTrue(manifest[key]["source"].startswith("local_game_"), key)
        pets = {key for key in manifest if key.startswith("hatch_")}
        self.assertEqual(14, len(pets))
        for key in pets:
            self.assertEqual("ObjectInfo.icon", manifest[key]["unity_object_type"], key)
            self.assertTrue(manifest[key]["usage_status"].startswith("verified_exact_local_game_"), key)
        skills = {key for key in manifest if key.startswith("level_")}
        self.assertEqual(120, len(skills))
        for key in skills:
            self.assertEqual("Sprite", manifest[key]["unity_object_type"], key)
            self.assertEqual(
                "generated_from_exact_local_game_skill_sprite",
                manifest[key]["usage_status"],
                key,
            )

    def test_every_lua_item_uses_manifest_provided_icon_paths(self):
        definitions = (ROOT / "poptracker" / "scripts" / "checks.lua").read_text()
        manifest = json.loads((ROOT / "data" / "tracker_asset_manifest.json").read_text())
        active = {
            check["key"] for check in json.loads(
                (ROOT / "data" / "canonical_catalog.json").read_text()
            )["checks"]
        }
        for entry in manifest["assets"]:
            if entry["check_key"] not in active:
                continue
            for state in ("checked", "unchecked", "unavailable"):
                self.assertIn(entry["outputs"][state]["path"], definitions)

    def test_rendered_assets_are_content_deduplicated(self):
        manifest = json.loads((ROOT / "data" / "tracker_asset_manifest.json").read_text())
        paths_by_hash: dict[str, set[str]] = {}
        for output in (
            output
            for entry in manifest["assets"]
            for output in entry["outputs"].values()
        ):
            paths_by_hash.setdefault(output["sha256"], set()).add(output["path"])
        self.assertTrue(all(len(paths) == 1 for paths in paths_by_hash.values()))
        self.assertEqual(
            len(paths_by_hash),
            len({
                output["path"]
                for entry in manifest["assets"]
                for output in entry["outputs"].values()
            }),
        )

    def test_rendered_asset_directory_has_no_orphan_images(self):
        manifest = json.loads((ROOT / "data" / "tracker_asset_manifest.json").read_text())
        expected = {
            output["path"]
            for entry in manifest["assets"]
            for output in entry["outputs"].values()
        }
        support = {
            f"accessibility-indicator-{color}-{variant}.png"
            for color in ("red", "yellow", "green", "grey")
            for variant in ("medium", "small", "large", "xl")
        }
        actual = {
            path.name
            for path in (ROOT / "poptracker" / "images").glob("*.png")
            if path.name not in support
        }
        actual.discard("transparent.png")
        self.assertEqual(expected, actual)

    def test_access_logic_covers_every_check_and_goal_scope(self):
        catalog = json.loads((ROOT / "data" / "canonical_catalog.json").read_text())
        locations = json.loads(
            (ROOT / "poptracker" / "locations" / "locations.json").read_text()
        )
        self.assertEqual(
            {check["display_name"] for check in catalog["checks"]},
            {location["name"] for location in locations},
        )
        location_map = (ROOT / "poptracker" / "scripts" / "location_map.lua").read_text()
        for check in catalog["checks"]:
            self.assertIn(f'[{check["stable_id"]}]', location_map)
            self.assertIn(check["key"], location_map)
        logic = (ROOT / "poptracker" / "scripts" / "check_runtime.lua").read_text()
        for state in ("red", "yellow", "green", "grey"):
            self.assertIn(f'"{state}"', logic)
        runtime = (ROOT / "poptracker" / "scripts" / "check_runtime.lua").read_text()
        self.assertIn("FromImageReference", runtime)
        self.assertIn("accessibility-indicator-", runtime)
        self.assertNotIn("record.item.Name", runtime)
        self.assertIn(
            'local folder = checked and "check-icons-disabled" or "check-icons"',
            runtime,
        )
        variant_builder = (ROOT / "tools" / "build_tracker_variant_icons.py").read_text()
        self.assertIn(
            'for state, folder in (("checked", "check-icons"),',
            variant_builder,
        )
        self.assertIn(
            '("unchecked", "check-icons-disabled")):',
            variant_builder,
        )
        self.assertIn(
            'checked and "fallback-icon-disabled.png" or "fallback-icon.png"',
            runtime,
        )
        for state in ("red", "yellow", "green", "grey"):
            for variant in ("medium", "small", "large", "xl"):
                indicator = (
                    ROOT / "poptracker" / "images"
                    / f"accessibility-indicator-{state}-{variant}.png"
                )
                self.assertTrue(indicator.is_file(), indicator)
        autotracking = (
            ROOT / "poptracker" / "scripts" / "logic_autotracking.lua"
        ).read_text()
        self.assertIn("lower_wall = 0", autotracking)
        self.assertIn("defeat_all_bosses = 3", autotracking)

    def test_autotracking_uses_documented_callback_and_bulk_update_pattern(self):
        script = (ROOT / "poptracker" / "scripts" / "autotracking.lua").read_text()
        self.assertIn("Archipelago:AddClearHandler", script)
        self.assertIn("Archipelago:AddLocationHandler", script)
        self.assertIn("Archipelago.MissingLocations", script)
        self.assertIn("Archipelago.CheckedLocations", script)
        self.assertIn('ScriptHost:AddOnFrameHandler("Core Keeper initial location sync"', script)
        self.assertIn("sync_batch_size = 32", script)
        self.assertIn("(#missing + #checked) == 0", script)
        self.assertNotIn("Tracker.BulkUpdate", script)
        runtime = (ROOT / "poptracker" / "scripts" / "check_runtime.lua").read_text(encoding="utf-8")
        self.assertNotIn("IgnoreUserInput", runtime)
        runtime = (ROOT / "poptracker" / "scripts" / "check_runtime.lua").read_text()
        self.assertIn('Tracker:FindObjectForCode(definition.code)', runtime)
        self.assertIn("ScriptHost:AddWatchForCode", runtime)
        self.assertIn("record.item.Active = checked == true", runtime)
        self.assertNotIn("IgnoreUserInput", runtime)
        self.assertNotIn("Archipelago:LocationChecks", runtime)
        self.assertIn("SuppressCodeWatch", runtime)
        self.assertIn("FullRefreshDelayFrames = 2", runtime)
        self.assertIn("RefreshQueue", runtime)
        self.assertIn("VisualStates", runtime)
        logic_tracking = (ROOT / "poptracker" / "scripts" / "logic_autotracking.lua").read_text()
        self.assertIn('[8405000] = "progressive_workbench_license"', logic_tracking)
        self.assertIn('[8405002] = "progressive_anvil_license"', logic_tracking)
        self.assertIn('[8405003] = "progressive_furnace_license"', logic_tracking)
        self.assertNotIn('[8405019] = "progressive_workbench_license"', logic_tracking)
        self.assertIn("local MinimumMode = {", logic_tracking)
        self.assertIn("item.CurrentStage = randomized and 0 or Progressive[code]", logic_tracking)
        self.assertIn("item.Active = not randomized", logic_tracking)
        self.assertIn('golden_food = "goldensanity"', logic_tracking)
        self.assertIn('fish = "fishsanity"', logic_tracking)
        self.assertIn('option.Active = slot_data[slot_key] == true', logic_tracking)
        self.assertNotIn("enabled_location_groups", logic_tracking)
        self.assertNotIn("optional_bosses_enabled", logic_tracking)

    def test_randomizer_checks_hide_then_reveal_mapped_identity(self):
        reveal = (ROOT / "poptracker" / "scripts" / "randomizer_reveals.lua").read_text()
        init = (ROOT / "poptracker" / "scripts" / "init.lua").read_text()
        autotracking = (ROOT / "poptracker" / "scripts" / "autotracking.lua").read_text()
        runtime = (ROOT / "poptracker" / "scripts" / "check_runtime.lua").read_text()
        self.assertIn('ScriptHost:LoadScript("scripts/randomizer_reveals.lua")', init)
        self.assertIn("CK_CONFIGURE_RANDOMIZER_REVEALS(slot_data)", autotracking)
        self.assertIn('hidden_name = bare_name(source_record) .. " (???)"', reveal)
        self.assertIn("revealed_name = boss_title(source_boss.name, target_boss)", reveal)
        self.assertIn('GiantCicadaBoss={code="defeat_nimruza"', reveal)
        self.assertIn('display_icon_id = record.randomized.icon_id', runtime)
        self.assertNotIn('record.item.Name =', runtime)
        self.assertIn("display_icon_id = record.randomized.icon_id", runtime)

    def test_package_is_deterministic_and_rooted_at_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            first = Path(temporary) / "first.zip"
            second = Path(temporary) / "second.zip"
            package(ROOT / "poptracker", first)
            package(ROOT / "poptracker", second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(first) as archive:
                self.assertIn("manifest.json", archive.namelist())
                self.assertFalse(any(name.startswith("poptracker/") for name in archive.namelist()))
                packaged = set(archive.namelist())
                manifest = json.loads((ROOT / "data" / "tracker_asset_manifest.json").read_text())
                expected_images = {
                    "images/" + output["path"]
                    for entry in manifest["assets"]
                    for output in entry["outputs"].values()
                }
                self.assertLessEqual(expected_images, packaged)


if __name__ == "__main__":
    unittest.main()
