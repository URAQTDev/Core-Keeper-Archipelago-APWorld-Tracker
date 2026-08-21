"""Verify every physical reward candidate against the pinned runtime database."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from audit_prototype_check_targets import candidate_name_map


PHYSICAL_EFFECTS = {
    "tool_reward", "weapon_reward", "jewelry_reward", "accessory_reward", "armor_reward"
}

CORRECTIONS = {
    "Critter Pouch": ("CritterPouch", 0),
    "Medium Critter Pouch": ("MediumCritterPouch", 0),
    "Large Critter Pouch": ("LargeCritterPouch", 0),
    "Potion Pouch": ("PotionPouch", 0),
    "Medium Potion Pouch": ("MediumPotionPouch", 0),
    "Large Potion Pouch": ("LargePotionPouch", 0),
    "Morpha's Bubble Backpack": ("MorphaBag", 0),
    "Shellzooka": ("ScarabMortar", 0),
    "Storm Bringer": ("LightningGun", 0),
}


def build(items_path: Path, pools_path: Path, map_path: Path, runtime_path: Path) -> dict:
    items = json.loads(items_path.read_text(encoding="utf-8-sig"))
    pools = json.loads(pools_path.read_text(encoding="utf-8-sig"))
    names = {item["name"] for item in items if item["effect"] in PHYSICAL_EFFECTS}
    for pool in pools.values():
        names.update(pool["items"])

    candidates = candidate_name_map(map_path)
    candidates.update(CORRECTIONS)
    runtime = json.loads(runtime_path.read_text(encoding="utf-8-sig"))
    runtime_by_key = {
        (record["internal_name"], record["variation"]): record for record in runtime["records"]
    }
    records = []
    for name in sorted(names):
        candidate = candidates.get(name)
        game_record = runtime_by_key.get(candidate) if candidate else None
        records.append(
            {
                "display_name": name,
                "status": "runtime_verified" if game_record else "unresolved_candidate",
                "internal_name": candidate[0] if candidate else None,
                "variation": candidate[1] if candidate else None,
                "object_id": game_record["object_id"] if game_record else None,
            }
        )
    return {
        "schema_version": 1,
        "core_keeper_steam_build_id": runtime["core_keeper_steam_build_id"],
        "counts": {
            status: sum(record["status"] == status for record in records)
            for status in sorted({record["status"] for record in records})
        },
        "records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("items", type=Path)
    parser.add_argument("reward_pools", type=Path)
    parser.add_argument("candidate_name_map", type=Path)
    parser.add_argument("runtime_database", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = build(
        args.items, args.reward_pools, args.candidate_name_map, args.runtime_database
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
