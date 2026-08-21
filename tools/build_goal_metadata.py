"""Derive required boss counts for goal option descriptions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build(goal_path: Path, progression_path: Path) -> dict[str, Any]:
    policy = json.loads(goal_path.read_text(encoding="utf-8-sig"))
    progression = json.loads(progression_path.read_text(encoding="utf-8-sig"))
    bosses = {entry["key"]: entry for entry in progression["bosses"]}
    milestones = {entry["key"]: entry for entry in progression["milestones"]}

    def boss_closure(key: str, seen: set[str]) -> None:
        if key in seen:
            return
        if key == "all_bosses":
            for boss_key in bosses:
                boss_closure(boss_key, seen)
            return
        node = bosses.get(key) or milestones.get(key)
        if node is None:
            return  # license, merchant, and other non-boss requirements
        if key in bosses:
            seen.add(key)
        for requirement in node["requires_all"]:
            boss_closure(requirement, seen)

    goals = []
    for goal in policy["goals"]:
        required: set[str] = set()
        boss_closure(goal["terminal"], required)
        goals.append(
            {
                **goal,
                "required_boss_checks": len(required),
                "required_boss_keys": sorted(required),
                "hover_description": f"{goal['description']} Required boss checks: {len(required)}.",
            }
        )
    return {"schema_version": 1, "default_goal": policy["default_goal"], "goals": goals}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("goal_policy", type=Path)
    parser.add_argument("progression_policy", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = build(args.goal_policy, args.progression_policy)
    args.output.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
