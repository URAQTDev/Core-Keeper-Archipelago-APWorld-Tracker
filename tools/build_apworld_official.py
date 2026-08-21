"""Package the main-version world with Archipelago's Build APWorlds component."""

from __future__ import annotations

import argparse
import importlib.util
import logging
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path


FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def normalize_apworld(source: Path, output: Path) -> None:
    """Rewrite the official package with stable ordering and ZIP metadata."""
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=output.parent, suffix=".apworld", delete=False) as temporary:
        temporary_path = Path(temporary.name)
    try:
        with zipfile.ZipFile(source, "r") as incoming, zipfile.ZipFile(
            temporary_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
        ) as outgoing:
            for name in sorted(incoming.namelist()):
                original = incoming.getinfo(name)
                info = zipfile.ZipInfo(name, FIXED_ZIP_TIME)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = (0o755 if name.endswith("/") else 0o644) << 16
                info.flag_bits = original.flag_bits & 0x800
                outgoing.writestr(info, incoming.read(name), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        os.replace(temporary_path, output)
    finally:
        temporary_path.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archipelago", type=Path, required=True)
    parser.add_argument("--dependencies", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--build-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    sys.path[:0] = [str(args.dependencies.resolve()), str(args.archipelago.resolve())]
    args.build_root.mkdir(parents=True, exist_ok=True)
    staged_world = args.build_root / "worlds" / "core_keeper"
    if staged_world.exists():
        shutil.rmtree(staged_world)
    shutil.copytree(args.source, staged_world)

    import Utils

    scratch_user = args.build_root / "ap-user"
    (scratch_user / "worlds").mkdir(parents=True, exist_ok=True)
    Utils.user_path.cached_path = str(scratch_user)
    logging.disable(logging.CRITICAL)

    import worlds
    from worlds.AutoWorld import AutoWorldRegister

    AutoWorldRegister.world_types.pop("Core Keeper", None)
    package_name = "worlds.core_keeper_mainline_build"
    specification = importlib.util.spec_from_file_location(
        package_name,
        staged_world / "__init__.py",
        submodule_search_locations=[str(staged_world)],
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("Could not load staged Core Keeper APWorld.")
    package = importlib.util.module_from_spec(specification)
    sys.modules[package_name] = package
    specification.loader.exec_module(package)

    from worlds.LauncherComponents import components

    component = next(entry for entry in components if entry.display_name == "Build APWorlds")
    previous_directory = Path.cwd()
    try:
        os.chdir(args.build_root)
        assert component.func is not None
        component.func("Core Keeper", "--skip_open_folder")
    finally:
        os.chdir(previous_directory)

    built = args.build_root / "build" / "apworlds" / "core_keeper.apworld"
    if not built.exists():
        raise RuntimeError("Archipelago Build APWorlds did not produce core_keeper.apworld.")
    normalize_apworld(built, args.output)
    print(f"Built {args.output} using Archipelago's Build APWorlds component.")


if __name__ == "__main__":
    main()
