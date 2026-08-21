"""Build a compact, lossless index of ObjectID references in game configs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterator


def references(
    value: Any, path: str = "$", *, section: str | None = None
) -> Iterator[tuple[str, int, dict[str, Any]]]:
    if isinstance(value, dict):
        if isinstance(value.get("objectID"), int):
            # Preserve the containing record: fields such as weight, biome,
            # variation, and amount are required to interpret the reference.
            yield path, value["objectID"], value
        if section == "fishing" and path == "$" and isinstance(value.get("fish"), int):
            # Fishing definitions identify their result with `fish`, rather
            # than the `objectID` convention used by loot and spawn records.
            yield "$.fish", value["fish"], value
        for key, child in value.items():
            yield from references(child, f"{path}.{key}", section=section)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from references(child, f"{path}[{index}]", section=section)


def build(config_path: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    by_object: dict[int, list[list[Any]]] = {}
    sources: list[dict[str, Any]] = []
    for section in ("loot", "spawns", "fishing"):
        for source in config[section]:
            source_index = len(sources)
            sources.append(
                {"section": section, "source": source["source"], "sha256": source["sha256"]}
            )
            for path, object_id, container in references(source["payload"], section=section):
                by_object.setdefault(object_id, []).append([source_index, path, container])
    return {
        "schema_version": 1,
        "core_keeper_steam_build_id": config["core_keeper_steam_build_id"],
        "reference_tuple": ["source_index", "json_path", "containing_record"],
        "sources": sources,
        "objects": [
            {"object_id": object_id, "references": by_object[object_id]}
            for object_id in sorted(by_object)
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("game_config", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = build(args.game_config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
