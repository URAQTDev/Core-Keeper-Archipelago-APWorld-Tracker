"""Generate check-option counts and examples from the verified inventory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build(policy_path: Path, candidates_path: Path) -> dict[str, Any]:
    policy = json.loads(policy_path.read_text(encoding="utf-8-sig"))
    candidates = json.loads(candidates_path.read_text(encoding="utf-8-sig"))
    checks_by_group: dict[str, list[dict[str, Any]]] = {}
    for check in candidates["checks"]:
        checks_by_group.setdefault(check["group"], []).append(check)
    policy_keys = [group["key"] for group in policy["groups"]]
    if set(policy_keys) != set(checks_by_group):
        missing = sorted(set(checks_by_group) - set(policy_keys))
        extra = sorted(set(policy_keys) - set(checks_by_group))
        raise ValueError(f"check-group policy mismatch; missing={missing}, extra={extra}")

    groups = []
    for group in policy["groups"]:
        checks = sorted(checks_by_group[group["key"]], key=lambda item: item["stable_id"])
        examples = [check["display_name"] for check in checks[:3]]
        description = (
            f"Adds {len(checks)} checks. Examples: " + ", ".join(examples) + "."
        )
        groups.append({**group, "check_count": len(checks), "examples": examples, "description": description})
    return {"schema_version": 1, "groups": groups}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("policy", type=Path)
    parser.add_argument("check_candidates", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = build(args.policy, args.check_candidates)
    args.output.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
