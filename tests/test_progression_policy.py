import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ProgressionPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = json.loads((ROOT / "data" / "progression_policy.json").read_text(encoding="utf-8"))
        runtime = json.loads((ROOT / "data" / "runtime_database.raw.json").read_text(encoding="utf-8"))
        cls.runtime_names = {(row["object_id"], row["internal_name"]) for row in runtime["records"]}

    def test_boss_identities_are_runtime_verified(self):
        for boss in self.policy["bosses"]:
            self.assertIn((boss["object_id"], boss["internal_name"]), self.runtime_names)

    def test_progression_graph_is_acyclic(self):
        nodes = {entry["key"]: entry for entry in self.policy["milestones"] + self.policy["bosses"]}
        visiting = set()
        visited = set()

        def visit(key):
            if key not in nodes or key in visited:
                return
            self.assertNotIn(key, visiting, f"progression cycle includes {key}")
            visiting.add(key)
            for requirement in nodes[key]["requires_all"]:
                visit(requirement)
            visiting.remove(key)
            visited.add(key)

        for key in nodes:
            visit(key)

    def test_major_boss_chain_matches_design_contract(self):
        bosses = {entry["key"]: entry for entry in self.policy["bosses"]}
        self.assertEqual(["defeat_azeos", "fishing_workbench_license"], bosses["defeat_omoroth"]["requires_all"])
        self.assertEqual(["defeat_omoroth"], bosses["defeat_ra_akar"]["requires_all"])
        self.assertEqual(["defeat_druidra"], bosses["defeat_crydra"]["requires_all"])
        self.assertEqual(["defeat_crydra"], bosses["defeat_pyrdra"]["requires_all"])
        self.assertEqual(["defeat_second_titans"], bosses["defeat_core_commander"]["requires_all"])
        self.assertEqual(["defeat_nimruza"], bosses["defeat_sahabar"]["requires_all"])
        self.assertEqual(["defeat_nimruza"], bosses["defeat_oblidra"]["requires_all"])
        self.assertEqual(["lower_wall"], bosses["defeat_nimruza"]["sequence_break_all"])

    def test_four_major_progression_bands_cover_every_boss_once(self):
        spheres = self.policy["spheres"]
        self.assertEqual([1, 2, 3, 4], [entry["sphere"] for entry in spheres])
        self.assertEqual([5, 6, 5, 4], [len(entry["bosses"]) for entry in spheres])
        flattened = [boss for entry in spheres for boss in entry["bosses"]]
        self.assertEqual(len(flattened), len(set(flattened)))
        self.assertEqual({boss["key"] for boss in self.policy["bosses"]}, set(flattened))


if __name__ == "__main__":
    unittest.main()
