from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]


class DeathLinkTests(unittest.TestCase):
    def test_option_and_slot_data_contract(self) -> None:
        options = (ROOT / "apworld/core_keeper/options.py").read_text()
        world = (ROOT / "apworld/core_keeper/world.py").read_text()
        self.assertIn('display_name = "Death Link"', options)
        self.assertIn('option_death_link_keep_inventory = 2', options)
        self.assertIn('OptionGroup("Game Options", [DeathLink])', options)
        self.assertIn('"death_link": int(self.options.death_link)', world)

    def test_client_uses_official_service_and_native_death_state(self) -> None:
        connection = (ROOT / "client/ArchipelagoConnection.cs").read_text()
        controller = (ROOT / "client/Runtime/DeathLinkController.cs").read_text()
        self.assertIn("CreateDeathLinkService", connection)
        self.assertIn("EnableDeathLink", connection)
        self.assertIn("SendDeathLink", connection)
        self.assertIn("HealthCD", controller)
        self.assertIn("PlayerState.DeathStateCD", controller)
        self.assertIn("CharacterType.Casual", controller)
        self.assertIn("suppressOutgoingDeath", controller)


if __name__ == "__main__":
    unittest.main()
