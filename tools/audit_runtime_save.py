"""Compare an official server save with generated Core Keeper location metadata."""

from __future__ import annotations

import argparse
import ast
import json
import pickle
import sys
import zlib
from collections import defaultdict
from pathlib import Path


def literal_assignment(path: Path, name: str):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for statement in tree.body:
        if not isinstance(statement, ast.Assign):
            continue
        if any(isinstance(target, ast.Name) and target.id == name for target in statement.targets):
            return ast.literal_eval(statement.value)
    raise KeyError(name)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("save", type=Path)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--archipelago", type=Path, required=True)
    parser.add_argument("--dependencies", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    sys.path[:0] = [str(args.archipelago), str(args.dependencies)]
    # NetworkItem is referenced by the trusted local server pickle.
    import NetUtils  # noqa: F401

    locations_path = args.root / "apworld" / "core_keeper" / "locations.py"
    name_to_id = literal_assignment(locations_path, "LOCATION_NAME_TO_ID")
    metadata = literal_assignment(locations_path, "LOCATION_METADATA")
    id_to_name = {location_id: name for name, location_id in name_to_id.items()}

    saved = pickle.loads(zlib.decompress(args.save.read_bytes()))
    checked_ids = set(saved["location_checks"].get((0, 1), set()))
    excluded_groups = {"enemies", "bosses"}
    expected_names = {
        name for name, (group, _scope, _requirements) in metadata.items()
        if group not in excluded_groups
    }
    expected_ids = {name_to_id[name] for name in expected_names}
    checked_expected = checked_ids & expected_ids
    missing_ids = expected_ids - checked_ids

    checked_by_group: dict[str, list[str]] = defaultdict(list)
    missing_by_group: dict[str, list[str]] = defaultdict(list)
    for location_id in sorted(checked_expected):
        name = id_to_name[location_id]
        checked_by_group[metadata[name][0]].append(name)
    for location_id in sorted(missing_ids):
        name = id_to_name[location_id]
        missing_by_group[metadata[name][0]].append(name)

    report = {
        "save": str(args.save.resolve()),
        "expected_non_enemy_non_boss": len(expected_ids),
        "checked_non_enemy_non_boss": len(checked_expected),
        "missing_non_enemy_non_boss": len(missing_ids),
        "unexpected_checked": sorted(id_to_name.get(value, str(value)) for value in checked_ids - expected_ids),
        "groups": {
            group: {
                "expected": len(checked_by_group[group]) + len(missing_by_group[group]),
                "checked": len(checked_by_group[group]),
                "missing": missing_by_group[group],
            }
            for group in sorted(set(checked_by_group) | set(missing_by_group))
        },
    }
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered, end="")


if __name__ == "__main__":
    main()
