"""Join checked objects to authoritative recipe, loot, spawn, and fishing evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build(candidates_path: Path, runtime_path: Path, index_path: Path) -> dict[str, Any]:
    candidates = json.loads(candidates_path.read_text(encoding="utf-8-sig"))
    runtime = json.loads(runtime_path.read_text(encoding="utf-8-sig"))
    index = json.loads(index_path.read_text(encoding="utf-8-sig"))

    runtime_by_id: dict[int, list[dict[str, Any]]] = {}
    for record in runtime["records"]:
        runtime_by_id.setdefault(record["object_id"], []).append(record)
    config_by_id = {record["object_id"]: record["references"] for record in index["objects"]}

    stations_by_output: dict[int, list[dict[str, Any]]] = {}
    for station in runtime["records"]:
        for recipe in station["station_recipes"]:
            stations_by_output.setdefault(recipe["object_id"], []).append(
                {
                    "station_object_id": station["object_id"],
                    "station_internal_name": station["internal_name"],
                    "station_variation": station["variation"],
                    "recipe": recipe,
                }
            )

    checked_ids = sorted(
        {
            check["trigger"]["object_id"]
            for check in candidates["checks"]
            if "object_id" in check["trigger"]
        }
    )
    objects = []
    for object_id in checked_ids:
        variants = runtime_by_id[object_id]
        objects.append(
            {
                "object_id": object_id,
                "internal_names": sorted({record["internal_name"] for record in variants}),
                "variations": [
                    {
                        "variation": record["variation"],
                        "ingredients": record["ingredients"],
                    }
                    for record in sorted(variants, key=lambda item: item["variation"])
                ],
                "crafting_stations": sorted(
                    stations_by_output.get(object_id, []),
                    key=lambda item: (
                        item["station_object_id"], item["station_variation"]
                    ),
                ),
                "game_config_reference_count": len(config_by_id.get(object_id, [])),
                "game_config_sections": sorted(
                    {
                        index["sources"][reference[0]]["section"]
                        for reference in config_by_id.get(object_id, [])
                    }
                ),
            }
        )
    return {
        "schema_version": 1,
        "core_keeper_steam_build_id": runtime["core_keeper_steam_build_id"],
        "game_config_evidence": "game_evidence_index.json",
        "objects": objects,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("check_candidates", type=Path)
    parser.add_argument("runtime_database", type=Path)
    parser.add_argument("game_evidence_index", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = build(args.check_candidates, args.runtime_database, args.game_evidence_index)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
