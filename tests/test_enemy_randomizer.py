from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "core_keeper_enemy_randomizer",
    ROOT / "apworld" / "core_keeper" / "enemy_randomizer.py",
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class EnemyRandomizerTests(unittest.TestCase):
    def test_mapping_is_deterministic_complete_and_one_cycle(self) -> None:
        mapping = MODULE.build_enemy_mapping(20260804)
        self.assertEqual(47, len(mapping))
        self.assertEqual(set(mapping), set(mapping.values()))
        self.assertTrue(all(source != target for source, target in mapping.items()))
        self.assertTrue(all(mapping[target] != source for source, target in mapping.items()))
        visited = set()
        cursor = next(iter(mapping))
        while cursor not in visited:
            visited.add(cursor)
            cursor = mapping[cursor]
        self.assertEqual(set(mapping), visited)

    def test_difficulties_relax_late_enemy_safety_and_suppress_same_biome(self) -> None:
        biome = dict(MODULE.ENEMY_SLOTS)
        dangerous = [0, 0, 0, 0]
        same_biome = [0, 0, 0, 0]
        for difficulty in range(4):
            for seed in range(128):
                mapping = MODULE.build_enemy_mapping(seed, difficulty)
                dangerous[difficulty] += sum(
                    biome[source] <= 4 and biome[target] >= 10
                    for source, target in mapping.items()
                )
                same_biome[difficulty] += sum(
                    biome[source] == biome[target]
                    for source, target in mapping.items()
                )
        self.assertLess(dangerous[0], dangerous[1])
        self.assertLess(dangerous[1], dangerous[2])
        self.assertEqual(dangerous[2], dangerous[3])
        self.assertTrue(all(count < 32 for count in same_biome))

    def test_structural_and_scripted_slots_are_excluded(self) -> None:
        slots = {name for name, _ in MODULE.ENEMY_SLOTS}
        for excluded in ("Cocoon", "VoidLarvaCocoon", "SnarePlant"):
            self.assertNotIn(excluded, slots)

    def test_randomizer_difficulty_precedes_enemy_toggle(self) -> None:
        options = (ROOT / "apworld" / "core_keeper" / "options.py").read_text()
        self.assertIn("class RandomizerDifficulty", options)
        self.assertIn("class RandomizeEnemies", options)
        self.assertNotIn('OptionGroup("Randomizers"', options)
        self.assertNotIn("randomize_enemies: RandomizeEnemies", options)
        self.assertIn('1: "Defeat S.A.H.A.B.A.R"', options)

    def test_runtime_handles_new_and_saved_entities(self) -> None:
        source = (ROOT / "client" / "Runtime" / "EnemyRandomizer.cs").read_text()
        self.assertIn("authoritative enemy conversion and combat scaling", source)
        self.assertIn("API.Server.InstantiateObject", source)
        self.assertIn("manager.DestroyEntity(graphEntity)", source)
        self.assertIn("ComponentType.ReadOnly<EnemyCD>()", source)
        self.assertNotIn("private static void Prefix", source)

    def test_runtime_inherits_source_health_and_damage_budget(self) -> None:
        source = (ROOT / "client" / "Runtime" / "EnemyRandomizer.cs").read_text()
        self.assertIn("CaptureCombatBudget", source)
        self.assertIn("ApplyCombatBudget", source)
        self.assertIn("health.maxHealth = budget.MaxHealth", source)
        self.assertIn("(float)budget.Damage / targetDamage", source)
        self.assertIn("ScaleDamage(manager, entity, appliedScale)", source)
        self.assertIn("DamageEffectCD", source)
        self.assertIn("BehaviorAdjustedDamage", source)
        self.assertIn("attack.projectilesPerShot", source)
        self.assertIn("attack.timeBetweenDamageTicks", source)
        self.assertIn("ReadyAt = Time.unscaledTime + 0.5f", source)
        self.assertIn("TryResolveDamageScale", source)
        self.assertIn("OwnerReferenceCD", source)
        self.assertIn("Enemy combat budget", source)
        self.assertIn("RandomizedEnemySourceCD", source)
        self.assertIn("recovered saved source", source)
        self.assertIn("LevelEntitiesBuffer", source)
        self.assertIn("WeaponDamageCD", source)
        self.assertIn("ApplySourceLoot", source)
        self.assertIn("DropsLootFromLootTableCD", source)
        self.assertIn("CopyPrefabBuffer<DropsLootBuffer>", source)
        self.assertIn("normalizationLoggedSources.Add(pending.Source)", source)
        self.assertIn("healthTierScale", source)
        self.assertIn("Math.Min(pressureScale, healthTierScale)", source)
        self.assertIn("configuredDifficulty < 3", source)
        self.assertIn("ServerGuidCD", source)
        self.assertIn("RandomizedEnemyWorlds", source)
        self.assertIn("recoverInitialSnapshot", source)
        self.assertIn("recoveryInverse.TryGetValue(source, out savedOriginal)", source)
        self.assertIn("PersistRandomizedWorld(activeWorldKey)", source)
        self.assertIn("snapshotNotBefore = Time.unscaledTime + 5f", source)
        self.assertIn("candidateCount <= 0", source)
        self.assertIn("if (!initialSnapshotCaptured)", source)
        self.assertIn("initialSnapshotEntities.Count > 0 ? initialSnapshotEntities.Count : 24", source)
        self.assertIn("RandomizedEnemyWorldMappings", source)
        self.assertIn("recoveryInverse.TryGetValue(source, out savedOriginal)", source)
        self.assertIn("PersistWorldMapping(activeWorldGuid, configuredJson)", source)


if __name__ == "__main__":
    unittest.main()
