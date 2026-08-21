"""Normalize the accepted check inventory without importing prototype logic."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


NAME_CORRECTIONS = {
    "Collect Golden Larva Meat": "Collect Shiny Larva Meat",
    "Collect Dagger Fish": "Collect Dagger Fin",
    "Collect Litho Triolobite": "Collect Litho Trilobite",
}

GROUP_NAMES = {
    "blocks": "blocksanity",
    "figurines": "figurinesanity",
    "fish": "fishsanity",
    "golden_food": "goldensanity",
    "oracle_cards": "cardsanity",
    "skill_levels": "skillsanity",
    "valuables": "valuablesanity",
}


def trigger_for(name: str, record: dict) -> dict:
    if record["group"] == "skill_levels":
        match = re.fullmatch(r"Level (\d+) (.+)", name)
        if not match:
            raise ValueError(f"Invalid skill check name: {name}")
        return {"kind": "skill_level", "skill": match.group(2), "level": int(match.group(1))}
    if name.startswith("Unlock "):
        kind = "unlock"
    elif name.startswith("Hatch "):
        kind = "hatch"
    elif name.startswith("Talk to "):
        kind = "interact"
    elif name.startswith(("Slay ", "Defeat ")):
        kind = "kill"
    else:
        kind = "natural_acquisition"
    return {
        "kind": kind,
        "object_id": record["object_id"],
        "internal_name": record["internal_name"],
        "variation": record["variation"],
    }


def build(audit_path: Path) -> dict:
    audit = json.loads(audit_path.read_text(encoding="utf-8-sig"))
    checks = []
    for record in audit["records"]:
        name = NAME_CORRECTIONS.get(record["check_name"], record["check_name"])
        checks.append(
            {
                "display_name": name,
                "stable_id": record["stable_id"],
                "group": GROUP_NAMES.get(record["group"], record["group"]),
                "trigger": trigger_for(name, record),
                "goal_scope": None,
                "normal_logic": None,
                "sequence_break_logic": None,
                "status": "target_verified_logic_pending",
            }
        )
    return {
        "schema_version": 1,
        "core_keeper_steam_build_id": audit["core_keeper_steam_build_id"],
        "checks": checks,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("target_audit", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = build(args.target_audit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
