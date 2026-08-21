"""Validate and normalize the database exported by the in-game extractor.

The extractor is the authority for managed runtime metadata such as recipes.  This
import step binds that data to the pinned ObjectID catalog and makes the checked-in
artifact deterministic (the source file's timestamp and formatting are irrelevant).
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def normalize(runtime_path: Path, game_config_path: Path, source_manifest_path: Path) -> dict[str, Any]:
    runtime = json.loads(runtime_path.read_text(encoding="utf-8-sig"))
    game_config = json.loads(game_config_path.read_text(encoding="utf-8-sig"))
    manifest = json.loads(source_manifest_path.read_text(encoding="utf-8-sig"))

    if runtime.get("schema_version") != 1:
        raise ValueError("Unsupported runtime database schema")
    expected_build = manifest["core_keeper"]["steam_build_id"]
    if runtime.get("core_keeper_steam_build_id") != expected_build:
        raise ValueError("Runtime database does not match the pinned Core Keeper build")
    if game_config.get("core_keeper_steam_build_id") != expected_build:
        raise ValueError("Game configuration does not match the pinned Core Keeper build")

    id_by_name = {
        record["internal_name"]: record["object_id"]
        for record in game_config["object_ids"]["records"]
    }
    id_set = set(id_by_name.values())
    records = runtime.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("Runtime database contains no records")

    seen: set[tuple[int, int]] = set()
    runtime_ids: set[int] = set()
    for record in records:
        key = (record["object_id"], record["variation"])
        if key in seen:
            raise ValueError(f"Duplicate runtime object/variation {key}")
        seen.add(key)
        runtime_ids.add(record["object_id"])
        expected_id = id_by_name.get(record["internal_name"])
        if expected_id != record["object_id"]:
            raise ValueError(f"ObjectID mismatch for {record['internal_name']}")
        for ingredient in record["ingredients"]:
            if ingredient["object_id"] not in id_set or ingredient["amount"] <= 0:
                raise ValueError(f"Invalid ingredient on {record['internal_name']}: {ingredient}")

    ordered = sorted(records, key=lambda record: (record["object_id"], record["variation"]))
    source_payload = canonical_bytes(runtime)
    unresolved_station_ids = sorted(
        {
            recipe["object_id"]
            for record in ordered
            for recipe in record["station_recipes"]
            if recipe["object_id"] not in runtime_ids
        }
    )
    return {
        "schema_version": 1,
        "core_keeper_steam_build_id": expected_build,
        "source": {
            "kind": "in_game_managed_database",
            "record_count": len(ordered),
            "normalized_source_sha256": sha256_bytes(source_payload),
            "object_id_catalog_sha256": game_config["object_ids"]["sha256"],
        },
        # Some station buffers contain internal crafting actions which are not
        # ObjectID-backed prefabs. Preserve them verbatim and identify them here.
        "unresolved_internal_station_recipe_ids": unresolved_station_ids,
        "records": ordered,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("runtime_export", type=Path)
    parser.add_argument("game_config", type=Path)
    parser.add_argument("source_manifest", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    normalized = normalize(args.runtime_export, args.game_config, args.source_manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical_bytes(normalized))


if __name__ == "__main__":
    main()
