import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "core_keeper_boss_randomizer",
    ROOT / "apworld" / "core_keeper" / "boss_randomizer.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class BossRandomizerTests(unittest.TestCase):
    def test_mapping_is_deterministic_complete_derangement(self):
        first = MODULE.build_boss_mapping(20260805)
        second = MODULE.build_boss_mapping(20260805)
        self.assertEqual(first, second)
        self.assertEqual(set(first), set(MODULE.BOSS_SLOTS))
        self.assertEqual(set(first.values()), set(MODULE.BOSS_SLOTS))
        self.assertTrue(all(source != target for source, target in first.items()))

    def test_mapping_is_one_cycle(self):
        mapping = MODULE.build_boss_mapping(17)
        start = MODULE.BOSS_SLOTS[0]
        visited = set()
        current = start
        while current not in visited:
            visited.add(current)
            current = mapping[current]
        self.assertEqual(current, start)
        self.assertEqual(visited, set(MODULE.BOSS_SLOTS))

    def test_option_and_slot_data_contract(self):
        options = (ROOT / "apworld" / "core_keeper" / "options.py").read_text()
        world = (ROOT / "apworld" / "core_keeper" / "world.py").read_text()
        self.assertIn('display_name = "Randomize Bosses"', options)
        self.assertNotIn('OptionGroup("Randomizers"', options)
        self.assertNotIn("randomize_bosses: RandomizeBosses", options)
        self.assertIn('"randomize_bosses": False', world)
        self.assertIn('"boss_randomizer_map": build_boss_mapping(boss_seed)', world)

    def test_client_contract(self):
        connection = (ROOT / "client" / "ArchipelagoConnection.cs").read_text()
        entry = (ROOT / "client" / "ModEntryPoint.cs").read_text()
        observer = (ROOT / "client" / "Runtime" / "EnemyDeathObserver.cs").read_text()
        self.assertIn('ParseToggle(successful.SlotData, "randomize_bosses")', connection)
        self.assertIn('"boss_randomizer_map"', connection)
        self.assertIn("BossRandomizer.Configure", entry)
        self.assertIn("BossRandomizer.OriginalFor(originalId)", observer)

    def test_runtime_preserves_scripted_encounters_titles_and_reload_identity(self):
        runtime = (ROOT / "client" / "Runtime" / "BossRandomizer.cs").read_text()
        enemy = (ROOT / "client" / "Runtime" / "EnemyRandomizer.cs").read_text()
        self.assertIn("HydraBossBuriedCombatStateCD", runtime)
        self.assertIn("isAboveWater", runtime)
        self.assertIn("HasNearbyPlayer(manager, entity, players, ActivationDistance)", runtime)
        self.assertIn("ghorm.currentPhase = 1", runtime)
        self.assertIn('return "King " + name', runtime)
        self.assertIn('return "Commander " + name', runtime)
        self.assertIn('", Queen of the Burrowed Sands"', runtime)
        self.assertIn('string.Join("."', runtime)
        self.assertIn("new NameCD { Value = new FixedString64Bytes(title) }", runtime)
        self.assertIn("TryRecoverSavedReplacement", runtime)
        self.assertIn("ScaleCicadaSpawns", runtime)
        self.assertIn("RandomizedBossSaveRecords", runtime)
        self.assertIn("ScaleExternalSpawn", enemy)
        self.assertIn("GiantCicadaSlamArmsStateCD", enemy)
        self.assertIn("ownedDamageWorld != world", enemy)
        self.assertIn("ownedDamageWorld.IsCreated", enemy)
        self.assertLess(enemy.index("ApplyPendingBudgets();"), enemy.index("if (!enabled)"))


if __name__ == "__main__":
    unittest.main()
