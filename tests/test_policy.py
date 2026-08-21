from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
FORBIDDEN_WIKI_HOSTS = ("fandom" + ".com", "atma" + ".gg")
EXCLUDED_ROOTS = {".deps", ".nuget", ".tools", "build", "dist", "bin", "obj"}


def is_project_source(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    return path.is_file() and not any(part in EXCLUDED_ROOTS for part in relative.parts)


class PolicyTests(unittest.TestCase):
    def test_option_groups_preserve_approved_user_facing_order(self) -> None:
        options = (ROOT / "apworld" / "core_keeper" / "options.py").read_text(encoding="utf-8")
        declarations = options[
            options.index("class CoreKeeperOptions"):
            options.index("option_groups = [")
        ]
        groups = options[options.index("option_groups = ["):]
        self.assertLess(groups.index('OptionGroup("Checks (Default)"'), groups.index('OptionGroup("Rewards (Items)"'))
        expected_sections = {
            "Checks (Default)": ["RawMaterials", "RefinedMaterials", "LockedChests", "Seeds", "Food", "Enemies"],
            "Checks (Optional)": ["UniqueMaterials", "KeyItems", "Bosses", "Merchantsanity", "Petsanity", "Blocksanity", "Goldensanity", "Critters", "CattleMutilation"],
            "Checks (Sanity)": ["Skillsanity", "Fishsanity", "Figurinesanity", "Cardsanity", "Valuablesanity", "Toolsanity", "Weaponsanity", "Jewelrysanity", "Accessanity", "Armorsanity"],
        }
        section_positions = [groups.index(f'OptionGroup("{name}"') for name in expected_sections]
        self.assertEqual(sorted(section_positions), section_positions)
        for name, expected_checks in expected_sections.items():
            start = groups.index(f'OptionGroup("{name}"')
            end = groups.index("    ]),", start)
            checks = groups[start:end]
            positions = [checks.index(f"        {check},") for check in expected_checks]
            self.assertEqual(sorted(positions), positions, name)
        declaration_names = [
            "raw_materials", "refined_materials", "locked_chests", "seeds", "food",
            "enemies", "unique_materials", "key_items", "bosses",
            "merchantsanity", "petsanity", "blocksanity",
            "goldensanity", "critters", "cattle_mutilation", "skillsanity",
            "fishsanity", "figurinesanity", "cardsanity", "valuablesanity", "toolsanity",
            "weaponsanity", "jewelrysanity", "accessanity", "armorsanity",
        ]
        declaration_positions = [
            declarations.index(f"    {name}:") for name in declaration_names
        ]
        self.assertEqual(sorted(declaration_positions), declaration_positions)

        item_rewards = groups[groups.index('OptionGroup("Rewards (Items)"'):groups.index('OptionGroup("Rewards (Caches)"')]
        cache_rewards = groups[groups.index('OptionGroup("Rewards (Caches)"'):groups.index('OptionGroup("Quality of Life"')]
        self.assertIn("        RewardArmor,", item_rewards)
        legendary_classes = ["SoulSeekerCache", "TitanBreathCache", "PhantomSparkCache", "RuneSongCache", "CredenceOfRuinCache", "StormbringerCache"]
        positions = [cache_rewards.index(f"        {name},") for name in legendary_classes]
        self.assertEqual(sorted(positions), positions)
        self.assertLess(cache_rewards.index("        EmptyCacheWeight,"), positions[0])
        self.assertLess(cache_rewards.index("        AutomationCacheWeight,"), cache_rewards.index("        EmptyCacheWeight,"))
        quality_of_life = groups[groups.index('OptionGroup("Quality of Life"'):]
        self.assertLess(
            quality_of_life.index("        SkillXpMultiplier,"),
            quality_of_life.index("        InfiniteMerchantStock,"),
        )
        self.assertLess(
            quality_of_life.index("        PreventPriorityInOptionalChecks,"),
            quality_of_life.index("        PreventPriorityInSanity,"),
        )
        self.assertNotIn("        SkillXpMultiplier,", item_rewards + cache_rewards)
        self.assertIn('display_name = "Prevent Progression in Optional Checks"', options)
        self.assertIn('display_name = "Prevent Progression in Sanity"', options)
        self.assertIn('OptionGroup("Game Options", [DeathLink])', groups)
        self.assertNotIn('OptionGroup("Randomizers"', groups)

        for old_name in ("Merchantsanity", "Petsanity", "Blocksanity", "Goldensanity"):
            self.assertNotIn(f'display_name = "{old_name}"', options)
        for new_name in ("Merchants", "Pets", "Fishsanity", "Blocks", "Golden Food"):
            self.assertIn(f'display_name = "{new_name}"', options)

    def test_release_compliance_matrix_has_no_pending_or_blocked_rows(self) -> None:
        matrix = (ROOT / "spec" / "COMPLIANCE_MATRIX.md").read_text(encoding="utf-8")
        requirement_rows = [line for line in matrix.splitlines() if line.startswith("|")][2:]
        self.assertTrue(requirement_rows)
        for row in requirement_rows:
            with self.subTest(row=row):
                self.assertTrue(row.rstrip().endswith("| verified |"))

    def test_playtest_inventory_names_every_canonical_group(self) -> None:
        catalog = json.loads((ROOT / "data" / "canonical_catalog.json").read_text(encoding="utf-8"))
        playtest = (ROOT / "PLAYTEST.md").read_text(encoding="utf-8").casefold()
        for group in {check["group"] for check in catalog["checks"]}:
            display = group.replace("_", " ")
            with self.subTest(group=group):
                self.assertIn(display, playtest)

    def test_handoff_documents_match_active_tracker_and_focused_room(self) -> None:
        tracker = json.loads((ROOT / "poptracker" / "manifest.json").read_text(encoding="utf-8"))
        rooms = json.loads((ROOT / "playtest" / "focused_rooms.json").read_text(encoding="utf-8"))
        active = rooms["rooms"][0]
        self.assertEqual("critters", active["group"])

        checkpoint = (ROOT / "RESUME_CHECKPOINT.md").read_text(encoding="utf-8")
        playtest = (ROOT / "PLAYTEST.md").read_text(encoding="utf-8")
        self.assertIn(tracker["package_version"], checkpoint)
        self.assertIn(str(active["seed"]), checkpoint)
        self.assertIn(active["archive"], checkpoint)
        self.assertIn(f"Critters {active['check_count']}", checkpoint)
        self.assertIn("focused Critters room", playtest)

    def test_json_files_parse(self) -> None:
        for path in ROOT.rglob("*.json"):
            if not is_project_source(path):
                continue
            with self.subTest(path=path.relative_to(ROOT)):
                json.loads(path.read_text(encoding="utf-8-sig"))

    def test_mainline_source_does_not_reference_wikis(self) -> None:
        allowed = {
            ROOT / "README.md",
            ROOT / "spec" / "EVIDENCE_POLICY.md",
        }
        for path in ROOT.rglob("*"):
            if not is_project_source(path) or path in allowed or path.suffix == ".json":
                continue
            if path.suffix not in {".py", ".ps1", ".cs", ".lua", ".md"}:
                continue
            with self.subTest(path=path.relative_to(ROOT)):
                contents = path.read_text(encoding="utf-8-sig").casefold()
                for host in FORBIDDEN_WIKI_HOSTS:
                    self.assertNotIn(host, contents)

    def test_blocked_runtime_findings_record_the_required_next_evidence(self) -> None:
        findings = json.loads(
            (ROOT / "data" / "runtime_hook_findings.json").read_text(encoding="utf-8")
        )
        allowed = {"verified", "observed", "unverified", "blocked"}
        self.assertTrue(findings["findings"])
        for finding in findings["findings"]:
            self.assertIn(finding["status"], allowed)
            if finding["status"] in {"blocked", "unverified"}:
                self.assertTrue(finding["next_evidence_needed"])


if __name__ == "__main__":
    unittest.main()
