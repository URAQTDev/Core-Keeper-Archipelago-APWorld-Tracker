"""One-click local Core Keeper PopTracker asset installer for Windows."""

from __future__ import annotations

import os
import argparse
import contextlib
import io
import runpy
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import winreg
from pathlib import Path

# Explicit imports ensure the frozen setup executable includes Pillow codecs
# used by the bundled asset recipes.
from PIL import Image, ImageDraw, ImageEnhance, ImageOps, PngImagePlugin  # noqa: F401


APP_ID = "1621690"
PACK_NAME = "core_keeper_poptracker_local.zip"
PUBLIC_LOG = Path(os.environ.get("PUBLIC", "C:/Users/Public")) / "Documents/CoreKeeperArchipelago-Tracker-Setup.log"


class ProgressDots:
    def __init__(self) -> None:
        self.stopped = threading.Event()
        self.stream = sys.stdout
        self.thread = threading.Thread(target=self._display, daemon=True)

    def _display(self) -> None:
        # Short operations need no animation. If the wait lasts long enough to
        # need feedback, reveal one ellipsis in place on its own clean line.
        if self.stopped.wait(2):
            return
        count = 0
        while not self.stopped.is_set():
            count = (count + 1) % 4
            self.stream.write("\r" + ("." * count) + (" " * (3 - count)) + "\r")
            self.stream.flush()
            self.stopped.wait(1)

    def __enter__(self) -> "ProgressDots":
        self.thread.start()
        return self

    def __exit__(self, *_: object) -> None:
        self.stopped.set()
        self.thread.join()
        self.stream.write("\r   \r")
        self.stream.flush()


class Tee:
    def __init__(self, *streams: object) -> None:
        self.streams = streams

    def write(self, text: str) -> int:
        for stream in self.streams:
            stream.write(text)  # type: ignore[attr-defined]
        return len(text)

    def flush(self) -> None:
        for stream in self.streams:
            stream.flush()  # type: ignore[attr-defined]


def payload_root() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))


def steam_roots() -> list[Path]:
    candidates = [
        Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "Steam",
        Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Steam",
    ]
    roots: list[Path] = []
    for steam in candidates:
        if steam.is_dir() and steam not in roots:
            roots.append(steam)
        libraries = steam / "steamapps/libraryfolders.vdf"
        if libraries.is_file():
            for line in libraries.read_text(encoding="utf-8", errors="ignore").splitlines():
                if '"path"' not in line:
                    continue
                parts = line.split('"')
                if len(parts) >= 4:
                    library = Path(parts[3].replace("\\\\", "\\"))
                    if library.is_dir() and library not in roots:
                        roots.append(library)
    return roots


def find_game() -> Path:
    for root in steam_roots():
        candidate = root / "steamapps/common/Core Keeper"
        if (candidate / "CoreKeeper.exe").is_file():
            return candidate
    entered = input("Core Keeper was not found automatically. Paste its installation folder: ").strip().strip('"')
    candidate = Path(entered)
    if not (candidate / "CoreKeeper.exe").is_file():
        raise RuntimeError("That folder does not contain CoreKeeper.exe.")
    return candidate


def process_running(image_name: str) -> bool:
    result = subprocess.run(
        ["tasklist", "/FI", f"IMAGENAME eq {image_name}"],
        capture_output=True, text=True, check=False,
    )
    return image_name.lower() in result.stdout.lower()


def run_recipe(script: str, *arguments: Path | str) -> None:
    old_argv = sys.argv
    try:
        sys.argv = [script, *(str(argument) for argument in arguments)]
        runpy.run_path(str(payload_root() / "tools" / script), run_name="__main__")
    finally:
        sys.argv = old_argv


def run_recipe_with_progress(script: str, *arguments: Path | str) -> None:
    run_recipes_with_progress(((script, arguments),))


def run_recipes_with_progress(
    recipes: tuple[tuple[str, tuple[Path | str, ...]], ...],
) -> None:
    captured_output = io.StringIO()
    captured_error = io.StringIO()
    progress = ProgressDots()
    progress.__enter__()
    try:
        with contextlib.redirect_stdout(captured_output), contextlib.redirect_stderr(captured_error):
            for script, arguments in recipes:
                run_recipe(script, *arguments)
    except BaseException:
        progress.__exit__()
        sys.stdout.write(captured_output.getvalue())
        sys.stderr.write(captured_error.getvalue())
        raise
    else:
        progress.__exit__()
        sys.stdout.write(captured_output.getvalue())
        sys.stderr.write(captured_error.getvalue())
        sys.stdout.flush()
        sys.stderr.flush()


def user_profiles() -> list[Path]:
    root = Path(os.environ.get("SystemDrive", "C:")) / "Users"
    if not root.is_dir():
        return [Path.home()]
    profiles = [path for path in root.iterdir() if path.is_dir()]
    current = Path.home()
    return [current, *(path for path in profiles if path != current)]


def candidate_export_roots() -> list[Path]:
    roots = [
        profile / "AppData/LocalLow/Pugstorm/Core Keeper/CoreKeeperArchipelago"
        for profile in user_profiles()
    ]
    return list(dict.fromkeys(roots))


def export_complete(export_root: Path, started: float) -> bool:
    required = (
        export_root / "runtime_database.raw.json",
        export_root / "object-icons/manifest.json",
        export_root / "creature-icons/manifest.json",
        export_root / "boss-summon-icons/manifest.json",
        export_root / "skill-icons/manifest.json",
        export_root / "pet-skins/manifest.json",
    )
    return all(path.is_file() and path.stat().st_mtime >= started for path in required)


def wait_for_export(started: float) -> Path:
    deadline = time.time() + 240
    while time.time() < deadline:
        for export_root in candidate_export_roots():
            if export_complete(export_root, started):
                return export_root
        time.sleep(2)
    raise RuntimeError("Core Keeper did not finish exporting tracker assets within four minutes.")


def documents_candidates() -> list[Path]:
    candidates: list[Path] = []
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders",
        ) as key:
            personal, _ = winreg.QueryValueEx(key, "Personal")
            candidates.append(Path(os.path.expandvars(personal)))
    except OSError:
        pass
    for variable in ("OneDriveCommercial", "OneDriveConsumer", "OneDrive"):
        value = os.environ.get(variable)
        if value:
            candidates.append(Path(value) / "Documents")
    for profile in user_profiles():
        candidates.append(profile / "Documents")
        candidates.extend(profile.glob("OneDrive*/Documents"))
    return list(dict.fromkeys(candidates))


def find_documents_folder() -> Path:
    candidates = documents_candidates()
    for candidate in candidates:
        if (candidate / "PopTracker").is_dir():
            return candidate
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return Path.home() / "Documents"


def build_from_export(export_root: Path, output: Path) -> Path:
    base = payload_root()
    print("Building the textured PopTracker pack...")
    with tempfile.TemporaryDirectory(prefix="core-keeper-tracker-") as temporary:
        work = Path(temporary) / "mainline"
        shutil.copytree(base / "template", work)
        run_recipe("activate_local_tracker_assets.py", work)
        run_recipe("select_pet_skin_gradients.py", export_root)
        run_recipe_with_progress("import_runtime_object_icons.py", work, export_root / "object-icons")
        run_recipe("import_creature_loot_sprites.py", work, export_root / "creature-icons")
        run_recipe("import_boss_summon_icons.py", work, export_root / "boss-summon-icons")
        run_recipe("import_runtime_skill_icons.py", work, export_root / "skill-icons")
        run_recipe("import_runtime_license_icons.py", work, export_root)
        run_recipe("deduplicate_tracker_assets.py", work)
        output.parent.mkdir(parents=True, exist_ok=True)
        run_recipes_with_progress((
            ("build_tracker_variant_icons.py", (work, "--force")),
            ("build_tracker_indicators.py", (work,)),
            ("package_poptracker.py", (work / "poptracker", output)),
        ))
    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError(f"Tracker packaging did not create {output}.")
    return output


def remove_texture_free_packs(packs: Path, textured_pack: Path) -> None:
    patterns = (
        "core_keeper_poptracker_texture_free*.zip",
        "3-PopTracker-Pack-TEXTURE-FREE*.zip",
    )
    for pattern in patterns:
        for candidate in packs.glob(pattern):
            if candidate.resolve() != textured_pack.resolve():
                candidate.unlink()
                print(f"Removed replaced texture-free tracker pack: {candidate.name}")


def install() -> Path:
    base = payload_root()
    game = find_game()
    exporter_source = base / "extractor/CoreKeeperArchipelagoExtractor"
    exporter_target = game / "CoreKeeper_Data/StreamingAssets/Mods/CoreKeeperArchipelagoExtractor"
    documents = find_documents_folder()
    packs = documents / "PopTracker/packs"
    packs.mkdir(parents=True, exist_ok=True)

    if process_running("CoreKeeper.exe"):
        raise RuntimeError("Close Core Keeper before running tracker setup.")
    if exporter_target.exists():
        shutil.rmtree(exporter_target)
    shutil.copytree(exporter_source, exporter_target)
    started = time.time() - 1
    print("Launching Core Keeper to read its local tracker artwork...")
    os.startfile(f"steam://run/{APP_ID}")
    try:
        print("Waiting for Core Keeper to export artwork...")
        with ProgressDots():
            export_root = wait_for_export(started)
        print("Local Core Keeper artwork export completed.")
        print("Close Core Keeper to let setup remove the temporary extractor.")
        while process_running("CoreKeeper.exe"):
            time.sleep(2)
    finally:
        if not process_running("CoreKeeper.exe") and exporter_target.exists():
            shutil.rmtree(exporter_target)

    textured_pack = build_from_export(export_root, packs / PACK_NAME)
    remove_texture_free_packs(packs, textured_pack)
    return textured_pack


def run_main() -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--build-from-export", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--non-interactive", action="store_true")
    args = parser.parse_args()
    print("Core Keeper Archipelago Tracker Setup")
    print("This creates tracker artwork only from your installed copy of Core Keeper.\n")
    try:
        if args.build_from_export:
            if args.output is None:
                raise RuntimeError("--output is required with --build-from-export")
            output = build_from_export(args.build_from_export, args.output)
        else:
            output = install()
    except Exception as exception:
        print(f"\nSetup failed: {exception}")
        traceback.print_exc()
        print(f"Setup log: {PUBLIC_LOG}")
        if not args.non_interactive:
            input("Press Enter to close...")
        return 1
    print(f"\nTracker installed successfully:\n{output}")
    print("Open PopTracker and select (Textured) Core Keeper Archipelago Mainline, followed by its version number.")
    if not args.non_interactive:
        input("Press Enter to close...")
    return 0


def main() -> int:
    PUBLIC_LOG.parent.mkdir(parents=True, exist_ok=True)
    with PUBLIC_LOG.open("a", encoding="utf-8") as log:
        log.write(f"\n--- setup started {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        with contextlib.redirect_stdout(Tee(sys.stdout, log)), contextlib.redirect_stderr(Tee(sys.stderr, log)):
            return run_main()


if __name__ == "__main__":
    raise SystemExit(main())
