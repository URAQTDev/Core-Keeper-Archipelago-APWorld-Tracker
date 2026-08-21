"""Run the isolated main-version APWorld through Archipelago's test base."""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import logging
import sys
import unittest
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archipelago", type=Path, required=True)
    parser.add_argument("--dependencies", type=Path, required=True)
    parser.add_argument("--scratch", type=Path, required=True)
    args = parser.parse_args()

    world_root = Path(__file__).parents[1] / "apworld" / "core_keeper"
    sys.path[:0] = [str(args.dependencies), str(args.archipelago)]

    import Utils

    args.scratch.mkdir(parents=True, exist_ok=True)
    (args.scratch / "worlds").mkdir(exist_ok=True)
    Utils.user_path.cached_path = str(args.scratch)
    logging.disable(logging.CRITICAL)

    import worlds
    from worlds.AutoWorld import AutoWorldRegister

    # A prototype copy may exist in the developer checkout. The isolated main
    # package is loaded under a temporary module name while retaining its real
    # game name, so official WorldTestBase behavior is exercised without
    # changing the checkout.
    AutoWorldRegister.world_types.pop("Core Keeper", None)
    package_name = "worlds.core_keeper_mainline"
    specification = importlib.util.spec_from_file_location(
        package_name,
        world_root / "__init__.py",
        submodule_search_locations=[str(world_root)],
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("Could not load the main-version Core Keeper APWorld.")
    package = importlib.util.module_from_spec(specification)
    sys.modules[package_name] = package
    specification.loader.exec_module(package)

    module = importlib.import_module(f"{package_name}.test.test_generation")
    suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
