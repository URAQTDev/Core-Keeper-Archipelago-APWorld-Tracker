"""Interpret checked-object config references with enums extracted from the game."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def reverse(values: dict[str, int]) -> dict[int, str]:
    return {value: name for name, value in values.items() if not name.startswith("__")}


def named(value: Any, names: dict[int, str]) -> dict[str, Any] | None:
    if not isinstance(value, int):
        return None
    return {"value": value, "name": names.get(value)}


def build(
    candidates_path: Path,
    config_path: Path,
    index_path: Path,
    enums_path: Path,
) -> dict[str, Any]:
    candidates = json.loads(candidates_path.read_text(encoding="utf-8-sig"))
    config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    index = json.loads(index_path.read_text(encoding="utf-8-sig"))
    enums = json.loads(enums_path.read_text(encoding="utf-8-sig"))
    if len({config["core_keeper_steam_build_id"], index["core_keeper_steam_build_id"], enums["core_keeper_steam_build_id"]}) != 1:
        raise ValueError("evidence inputs describe different Core Keeper builds")

    names = {key: reverse(enums["enums"][key]) for key in ("Biome", "Tileset", "TileType")}
    payload_by_source = {
        source["source"]: source["payload"]
        for section in ("loot", "spawns", "fishing")
        for source in config[section]
    }
    refs_by_id = {entry["object_id"]: entry["references"] for entry in index["objects"]}
    checked_ids = sorted(
        {
            check["trigger"]["object_id"]
            for check in candidates["checks"]
            if "object_id" in check["trigger"]
        }
    )
    objects = []
    for object_id in checked_ids:
        interpreted = []
        for source_index, path, container in refs_by_id.get(object_id, []):
            source = index["sources"][source_index]
            context: dict[str, Any] = {}
            if source["section"] == "spawns":
                spawn_check = payload_by_source[source["source"]].get("spawnCheck", {})
                context = {
                    "biome": named(spawn_check.get("biome"), names["Biome"]),
                    "tile_type": named(spawn_check.get("tileType"), names["TileType"]),
                    "tilesets": [named(value, names["Tileset"]) for value in spawn_check.get("tilesets", [])],
                }
            elif source["section"] == "loot" and "onlyDropsInBiome" in container:
                context = {"biome_filter": named(container["onlyDropsInBiome"], names["Biome"])}
            elif source["section"] == "fishing" and path == "$.fish":
                context = {"direct_fish_definition": True}
            interpreted.append(
                {
                    "section": source["section"],
                    "source": source["source"],
                    "json_path": path,
                    "context": context,
                }
            )
        objects.append({"object_id": object_id, "references": interpreted})
    return {
        "schema_version": 1,
        "core_keeper_steam_build_id": config["core_keeper_steam_build_id"],
        "inputs": {
            "game_config": "game_config.raw.json",
            "reference_index": "game_evidence_index.json",
            "game_enums": "game_enums.raw.json",
        },
        "objects": objects,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("check_candidates", type=Path)
    parser.add_argument("game_config", type=Path)
    parser.add_argument("game_evidence_index", type=Path)
    parser.add_argument("game_enums", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = build(args.check_candidates, args.game_config, args.game_evidence_index, args.game_enums)
    args.output.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
