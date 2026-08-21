"""Audit prototype check targets against the pinned in-game runtime database.

Prototype files supply requirements candidates only. A candidate is marked usable
only when its internal name, numeric ObjectID, and variation exist in the current
Core Keeper runtime export. Nothing unresolved is imported into the main catalog.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


QUOTED_ENTRY = re.compile(
    r'\["(?P<display>(?:[^"\\]|\\.)+)"\]\s*=\s*\{\s*"(?P<internal>[^"]+)"\s*,\s*(?P<variation>\d+)\s*\}'
)
BARE_ENTRY = re.compile(
    r'^\s*(?P<display>[A-Za-z][A-Za-z0-9_-]*)\s*=\s*\{\s*"(?P<internal>[^"]+)"\s*,\s*(?P<variation>\d+)\s*\}',
    re.MULTILINE,
)

# Corrections are accepted only when the named object/variation is present in
# the pinned runtime export below. They repair prototype spelling/display-name
# drift; they are not trusted as evidence by themselves.
RUNTIME_VERIFIED_CANDIDATE_CORRECTIONS = {
    "S.A.H.A.B.A.R's Mortar Housing": ("LegendaryMortarPart3", 0),
    "Golden Larva Meat": ("GoldenLarvaMeat", 0),
    "Dagger Fish": ("DaggerFin", 0),
    "Litho Triolobite": ("LithoTrilobite", 0),
    "Oblidra the Void Titan": ("HydraBossVoid", 0),
    "S.A.H.A.B.A.R": ("RobotBoss", 0),
    "Otherworldly Merchant": ("VoidMerchant", 0),
    "Shellzooka": ("ScarabMortar", 0),
    "Morpha's Bubble Backpack": ("MorphaBag", 0),
    "Potion Pouch": ("PotionPouch", 0),
    "Medium Potion Pouch": ("MediumPotionPouch", 0),
    "Large Potion Pouch": ("LargePotionPouch", 0),
    "Critter Pouch": ("CritterPouch", 0),
    "Medium Critter Pouch": ("MediumCritterPouch", 0),
    "Large Critter Pouch": ("LargeCritterPouch", 0),
}


def candidate_name_map(path: Path) -> dict[str, tuple[str, int]]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    text = payload["parse"]["wikitext"]["*"]
    result: dict[str, tuple[str, int]] = {}
    for match in QUOTED_ENTRY.finditer(text):
        display = json.loads('"' + match.group("display") + '"')
        result[display] = (match.group("internal"), int(match.group("variation")))
    for match in BARE_ENTRY.finditer(text):
        result[match.group("display")] = (match.group("internal"), int(match.group("variation")))
    return result


def audit(checks_path: Path, candidate_map_path: Path, runtime_path: Path) -> dict[str, Any]:
    checks = json.loads(checks_path.read_text(encoding="utf-8-sig"))
    candidates = candidate_name_map(candidate_map_path)
    candidates.update(RUNTIME_VERIFIED_CANDIDATE_CORRECTIONS)
    runtime = json.loads(runtime_path.read_text(encoding="utf-8-sig"))
    runtime_by_key = {
        (record["internal_name"], record["variation"]): record
        for record in runtime["records"]
    }
    records = []
    for check in checks:
        source_name = check.get("source_name")
        candidate = candidates.get(source_name)
        if check["group"] == "skill_levels":
            status = "verified_non_object_trigger"
            internal_name = None
            variation = None
            object_id = None
        elif candidate is None:
            status = "unresolved_candidate"
            internal_name = None
            variation = None
            object_id = None
        else:
            internal_name, variation = candidate
            verified = runtime_by_key.get(candidate)
            if verified is None:
                status = "rejected_not_in_runtime"
                object_id = None
            else:
                status = "runtime_verified"
                object_id = verified["object_id"]
        records.append(
            {
                "check_name": check["name"],
                "stable_id": check["id"],
                "group": check["group"],
                "source_name": source_name,
                "status": status,
                "internal_name": internal_name,
                "object_id": object_id,
                "variation": variation,
            }
        )
    counts = {
        status: sum(record["status"] == status for record in records)
        for status in sorted({record["status"] for record in records})
    }
    return {
        "schema_version": 1,
        "core_keeper_steam_build_id": runtime["core_keeper_steam_build_id"],
        "counts": counts,
        "records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("checks", type=Path)
    parser.add_argument("candidate_name_map", type=Path)
    parser.add_argument("runtime_database", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = audit(args.checks, args.candidate_name_map, args.runtime_database)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
