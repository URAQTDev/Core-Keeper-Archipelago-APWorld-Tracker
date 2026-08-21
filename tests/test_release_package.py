import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).parents[1]

spec = importlib.util.spec_from_file_location(
    "package_release", ROOT / "tools" / "package_release.py"
)
assert spec is not None and spec.loader is not None
RELEASE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(RELEASE)


def load_tracker_setup():
    setup_spec = importlib.util.spec_from_file_location(
        "tracker_local_setup", ROOT / "tools" / "tracker_local_setup.py"
    )
    assert setup_spec is not None and setup_spec.loader is not None
    module = importlib.util.module_from_spec(setup_spec)
    setup_spec.loader.exec_module(module)
    return module


class ReleasePackageTests(unittest.TestCase):
    def test_required_web_documents_exist_and_setup_matches_current_ui(self) -> None:
        docs = ROOT / "apworld" / "core_keeper" / "docs"
        game_info = docs / "en_Core Keeper.md"
        setup = docs / "setup_en.md"
        self.assertTrue(game_info.is_file())
        self.assertTrue(setup.is_file())
        self.assertIn("What does this randomizer do?", game_info.read_text(encoding="utf-8"))
        setup_text = setup.read_text(encoding="utf-8")
        self.assertIn("Settings", setup_text)
        self.assertIn("Archipelago", setup_text)
        self.assertIn("Save and Connect", setup_text)
        self.assertNotIn("press `F4`", setup_text)

    def test_mod_archive_is_deterministic_and_rooted(self) -> None:
        source = ROOT / "dist" / "CoreKeeperArchipelago"
        with tempfile.TemporaryDirectory() as temporary:
            first = Path(temporary) / "first.zip"
            second = Path(temporary) / "second.zip"
            RELEASE.write_mod_archive(source, first)
            RELEASE.write_mod_archive(source, second)
            self.assertEqual(
                hashlib.sha256(first.read_bytes()).digest(),
                hashlib.sha256(second.read_bytes()).digest(),
            )
            with ZipFile(first) as archive:
                names = archive.namelist()
            self.assertTrue(names)
            self.assertTrue(all(name.startswith("CoreKeeperArchipelago/") for name in names))
            self.assertIn("CoreKeeperArchipelago/ModManifest.json", names)

        notice = ROOT / "THIRD_PARTY_NOTICES.md"
        with tempfile.TemporaryDirectory() as temporary:
            archive_path = Path(temporary) / "licensed.zip"
            RELEASE.write_mod_archive(source, archive_path, notice)
            with ZipFile(archive_path) as archive:
                names = archive.namelist()
                notice_text = archive.read(
                    "CoreKeeperArchipelago/THIRD_PARTY_NOTICES.md"
                ).decode("utf-8")
            self.assertIn("Archipelago.MultiClient.Net", notice_text)
            self.assertIn("MIT License", notice_text)

    def test_modio_archive_has_manifest_at_zip_root(self) -> None:
        source = ROOT / "dist" / "CoreKeeperArchipelago"
        with tempfile.TemporaryDirectory() as temporary:
            first = Path(temporary) / "first-modio.zip"
            second = Path(temporary) / "second-modio.zip"
            RELEASE.write_modio_archive(source, first)
            RELEASE.write_modio_archive(source, second)
            self.assertEqual(
                hashlib.sha256(first.read_bytes()).digest(),
                hashlib.sha256(second.read_bytes()).digest(),
            )
            with ZipFile(first) as archive:
                names = archive.namelist()
            self.assertIn("ModManifest.json", names)
            self.assertIn("CoreKeeperArchipelago.dll", names)
            self.assertNotIn("CoreKeeperArchipelago/ModManifest.json", names)

    def test_component_versions_are_aligned(self) -> None:
        self.assertIn(
            '"world_version": "0.9.0-rc.8"',
            (ROOT / "apworld" / "core_keeper" / "archipelago.json").read_text(encoding="utf-8"),
        )
        self.assertIn(
            '"package_version": "0.9.0-rc.8"',
            (ROOT / "poptracker" / "manifest.json").read_text(encoding="utf-8"),
        )
        self.assertEqual("0.9.0-rc.8", RELEASE.VERSION)

    def test_release_uses_texture_free_tracker_distribution(self) -> None:
        packaging = (ROOT / "tools" / "package_release.py").read_text(encoding="utf-8")
        pipeline = (ROOT / "Build-Mainline.ps1").read_text(encoding="utf-8")
        self.assertIn("core_keeper_poptracker_texture_free_{VERSION}.zip", packaging)
        self.assertIn("CoreKeeperArchipelago-Tracker-Setup-{VERSION}.zip", packaging)
        self.assertNotIn('"core_keeper_poptracker.zip"', packaging)
        self.assertIn("build\\tracker-local-distribution\\template\\poptracker", pipeline)
        self.assertIn("Build-TrackerLocalSetup.ps1", pipeline)

    def test_complete_bundle_preserves_archipelago_compatible_apworld_name(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            release = root / "release"
            release.mkdir()
            files = {
                f"core_keeper_poptracker_texture_free_{RELEASE.VERSION}.zip": b"tracker",
                f"CoreKeeperArchipelago-Tracker-Setup-{RELEASE.VERSION}.zip": b"setup",
            }
            for name, content in files.items():
                (release / name).write_bytes(content)
            with ZipFile(release / "core_keeper.apworld", "w") as apworld:
                apworld.writestr("core_keeper/__init__.py", "")
            instructions = root / "START-HERE.txt"
            instructions.write_text("Release {VERSION}", encoding="utf-8")
            output = root / "complete.zip"
            RELEASE.write_complete_archive(release, output, instructions)
            with ZipFile(output) as archive:
                names = archive.namelist()
                self.assertIn("1-core_keeper.apworld", names)
                self.assertNotIn(
                    f"1-Core-Keeper-MOD-{RELEASE.VERSION}.zip", names
                )
                self.assertNotIn(
                    f"1-Core-Keeper-APWORLD-{RELEASE.VERSION}.apworld", names
                )
                self.assertEqual(
                    f"Release {RELEASE.VERSION}",
                    archive.read("START-HERE.txt").decode("utf-8"),
                )

    def test_tracker_setup_handles_cross_profile_paths_and_shows_activity(self) -> None:
        setup = (ROOT / "tools" / "tracker_local_setup.py").read_text(encoding="utf-8")
        self.assertIn("class ProgressDots", setup)
        self.assertIn("if self.stopped.wait(2):", setup)
        self.assertIn('self.stream.write("\\r" + ("." * count)', setup)
        self.assertNotIn("with ProgressDots(), tempfile.TemporaryDirectory", setup)
        self.assertIn('run_recipe_with_progress("import_runtime_object_icons.py"', setup)
        self.assertIn("run_recipes_with_progress((", setup)
        self.assertIn('(\"build_tracker_variant_icons.py\", (work, \"--force\"))', setup)
        self.assertIn('(\"package_poptracker.py\", (work / \"poptracker\", output))', setup)
        self.assertIn("candidate_export_roots", setup)
        self.assertIn("find_documents_folder", setup)
        self.assertIn("find_poptracker_pack_folders", setup)
        self.assertIn("wait_for_poptracker_to_close", setup)
        self.assertIn('process_running("PopTracker.exe")', setup)
        self.assertIn("remove_replaced_core_keeper_packs", setup)
        self.assertIn('PACK_UID = "core-keeper-archipelago-mainline"', setup)
        self.assertIn('profile / "Downloads"', setup)
        self.assertIn('profile / "Desktop"', setup)
        self.assertIn('root.rglob("poptracker.exe")', setup)
        self.assertIn("pack_uid(candidate) != PACK_UID", setup)
        self.assertIn("verify_textured_pack(destination, expected_hash)", setup)
        self.assertNotIn('folders.append(find_documents_folder() / "PopTracker/packs")', setup)
        self.assertIn("OneDriveCommercial", setup)
        self.assertIn("CoreKeeperArchipelago-Tracker-Setup.log", setup)

    def test_tracker_setup_replaces_same_uid_regardless_of_filename(self) -> None:
        setup = load_tracker_setup()
        with tempfile.TemporaryDirectory() as temporary:
            packs = Path(temporary)
            old_zip = packs / "totally-unexpected-old-name.zip"
            with ZipFile(old_zip, "w") as archive:
                archive.writestr(
                    "manifest.json",
                    json.dumps({"package_uid": setup.PACK_UID, "package_version": "99.0"}),
                )
            old_folder = packs / "unpacked-old-copy"
            old_folder.mkdir()
            (old_folder / "manifest.json").write_text(
                json.dumps({"package_uid": setup.PACK_UID}), encoding="utf-8"
            )
            unrelated = packs / "another-game.zip"
            with ZipFile(unrelated, "w") as archive:
                archive.writestr("manifest.json", json.dumps({"package_uid": "another-game"}))

            setup.remove_replaced_core_keeper_packs(packs)

            self.assertFalse(old_zip.exists())
            self.assertFalse(old_folder.exists())
            self.assertTrue(unrelated.exists())

    def test_tracker_setup_verifies_textured_pack_contents_and_hash(self) -> None:
        setup = load_tracker_setup()
        with tempfile.TemporaryDirectory() as temporary:
            pack = Path(temporary) / "textured.zip"
            with ZipFile(pack, "w") as archive:
                archive.writestr(
                    "manifest.json",
                    json.dumps({"package_uid": setup.PACK_UID, "name": "(Textured) Core Keeper"}),
                )
            expected = hashlib.sha256(pack.read_bytes()).hexdigest()
            setup.verify_textured_pack(pack, expected)
            with self.assertRaises(RuntimeError):
                setup.verify_textured_pack(pack, "not-the-file-hash")


if __name__ == "__main__":
    unittest.main()
