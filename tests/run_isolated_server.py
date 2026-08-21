"""Launch the official MultiServer with only the generated Core Keeper package.

The normal frozen server imports every APWorld installed on the workstation.
That makes a protocol test depend on unrelated third-party packages. This
runner keeps the official MultiServer implementation while supplying the one
data package embedded in this integration's deterministic test room.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import types
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archipelago", type=Path, required=True)
    parser.add_argument("--dependencies", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--multidata", type=Path, required=True)
    parser.add_argument("--savefile", type=Path, required=True)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args()

    sys.path[:0] = [str(args.dependencies), str(args.archipelago)]
    os.environ["SKIP_REQUIREMENTS_UPDATE"] = "1"

    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    item_name_to_id = {
        record["display_name"]: record["stable_id"]
        for record in catalog["rewards"]
    }
    location_name_to_id = {
        record["display_name"]: record["stable_id"]
        for record in catalog["checks"]
    }

    class CoreKeeperStub:
        item_name_groups: dict[str, set[str]] = {}
        location_name_groups: dict[str, set[str]] = {}
        hint_blacklist: frozenset[str] = frozenset()

    worlds = types.ModuleType("worlds")
    worlds.network_data_package = {
        "version": 0,
        "games": {
            "Core Keeper": {
                "item_name_to_id": item_name_to_id,
                "location_name_to_id": location_name_to_id,
                "item_name_groups": {},
                "location_name_groups": {},
            }
        },
    }
    worlds.AutoWorldRegister = types.SimpleNamespace(
        world_types={"Core Keeper": CoreKeeperStub}
    )
    sys.modules["worlds"] = worlds
    auto_world = types.ModuleType("worlds.AutoWorld")
    auto_world.AutoWorldRegister = worlds.AutoWorldRegister
    sys.modules["worlds.AutoWorld"] = auto_world

    import Utils

    isolated_user_path = args.savefile.parent / "server-user"
    isolated_user_path.mkdir(parents=True, exist_ok=True)
    Utils.user_path.cached_path = str(isolated_user_path)

    import MultiServer

    sys.argv = [
        "MultiServer.py",
        str(args.multidata),
        "--host",
        args.host,
        "--port",
        str(args.port),
        "--savefile",
        str(args.savefile),
        "--loglevel",
        "warning",
    ]
    asyncio.run(MultiServer.main(MultiServer.parse_args()))


if __name__ == "__main__":
    main()
