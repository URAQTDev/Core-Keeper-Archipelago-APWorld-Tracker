"""Build exact crafting alternatives for checked objects from runtime game data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build(
    candidates_path: Path, runtime_path: Path, license_policy_path: Path
) -> dict[str, Any]:
    candidates = json.loads(candidates_path.read_text(encoding="utf-8-sig"))
    runtime = json.loads(runtime_path.read_text(encoding="utf-8-sig"))
    policy = json.loads(license_policy_path.read_text(encoding="utf-8-sig"))
    if runtime["core_keeper_steam_build_id"] != policy["core_keeper_steam_build_id"]:
        raise ValueError("runtime database and license policy describe different builds")

    records_by_id: dict[int, list[dict[str, Any]]] = {}
    stations_by_output: dict[int, list[dict[str, Any]]] = {}
    for record in runtime["records"]:
        records_by_id.setdefault(record["object_id"], []).append(record)
        for recipe in record["station_recipes"]:
            stations_by_output.setdefault(recipe["object_id"], []).append(record)
    policy_by_station = {entry["object_id"]: entry for entry in policy["stations"]}
    checked_ids = sorted(
        {
            check["trigger"]["object_id"]
            for check in candidates["checks"]
            if "object_id" in check["trigger"]
        }
    )

    objects = []
    for object_id in checked_ids:
        variants = records_by_id[object_id]
        stations = []
        for station in sorted(
            stations_by_output.get(object_id, []),
            key=lambda item: (item["object_id"], item["variation"]),
        ):
            station_policy = policy_by_station.get(station["object_id"])
            stations.append(
                {
                    "object_id": station["object_id"],
                    "internal_name": station["internal_name"],
                    "variation": station["variation"],
                    "policy_status": (
                        "outside_license_system"
                        if station_policy is None
                        else "free"
                        if station_policy["license"] is None
                        else "licensed"
                    ),
                    "license": None if station_policy is None else station_policy["license"],
                    "license_stage": None if station_policy is None else station_policy["stage"],
                    "minimum_license_mode": None if station_policy is None else station_policy["minimum_mode"],
                }
            )
        objects.append(
            {
                "object_id": object_id,
                "internal_names": sorted({record["internal_name"] for record in variants}),
                "ingredient_variants": [
                    {
                        "variation": record["variation"],
                        "ingredients": record["ingredients"],
                    }
                    for record in sorted(variants, key=lambda item: item["variation"])
                    if record["ingredients"]
                ],
                "stations": stations,
                "is_craftable": bool(stations),
            }
        )
    return {
        "schema_version": 1,
        "core_keeper_steam_build_id": runtime["core_keeper_steam_build_id"],
        "inputs": {
            "check_candidates": "check_candidates.json",
            "runtime_database": "runtime_database.raw.json",
            "license_policy": "license_policy.json",
        },
        "objects": objects,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("check_candidates", type=Path)
    parser.add_argument("runtime_database", type=Path)
    parser.add_argument("license_policy", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = build(args.check_candidates, args.runtime_database, args.license_policy)
    args.output.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
