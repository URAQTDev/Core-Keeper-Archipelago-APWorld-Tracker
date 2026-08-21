"""Extract version-pinned Core Keeper configuration data without interpretation.

This extractor deliberately preserves internal identifiers. Display-name mapping,
progression logic, and Archipelago identities are separate reviewed steps.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


OBJECT_ID_PATTERN = re.compile(r'"(?P<name>[^"]+)"\s*:\s*(?P<value>-?\d+)')


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_id_map(path: Path) -> dict[str, int]:
    """Parse Core Keeper's comma-less ID map format."""
    pairs = [
        (match.group("name"), int(match.group("value")))
        for match in OBJECT_ID_PATTERN.finditer(path.read_text(encoding="utf-8-sig"))
    ]
    names = [name for name, _ in pairs]
    values = [value for _, value in pairs]
    if len(names) != len(set(names)):
        raise ValueError(f"Duplicate internal names in {path}")
    if len(values) != len(set(values)):
        raise ValueError(f"Duplicate numeric IDs in {path}")
    if not pairs:
        raise ValueError(f"No ID records found in {path}")
    return dict(pairs)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def extract_json_directory(path: Path, conf_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for source in sorted(path.rglob("*.json")):
        records.append(
            {
                "source": relative(source, conf_root),
                "sha256": sha256(source),
                "payload": load_json(source),
            }
        )
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("game_root", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--steam-build-id", type=int, required=True)
    args = parser.parse_args()

    conf_root = args.game_root / "CoreKeeper_Data" / "StreamingAssets" / "Conf"
    object_id_path = conf_root / "ID" / "ObjectID.json"
    object_ids = parse_id_map(object_id_path)

    output = {
        "schema_version": 1,
        "core_keeper_steam_build_id": args.steam_build_id,
        "object_ids": {
            "source": relative(object_id_path, conf_root),
            "sha256": sha256(object_id_path),
            "records": [
                {"internal_name": name, "object_id": object_id}
                for name, object_id in sorted(object_ids.items(), key=lambda pair: pair[1])
            ],
        },
        "loot": extract_json_directory(conf_root / "Loot", conf_root),
        "spawns": extract_json_directory(conf_root / "Spawn", conf_root),
        "fishing": extract_json_directory(conf_root / "Fishing", conf_root),
        "factions": extract_json_directory(conf_root / "Factions", conf_root),
        "talents": extract_json_directory(conf_root / "Talents", conf_root),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
