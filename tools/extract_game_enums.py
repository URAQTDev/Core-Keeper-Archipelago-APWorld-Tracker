"""Parse enum source emitted by the pinned ILSpy tool into deterministic JSON."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


MEMBER = re.compile(r"^(?P<name>[A-Za-z_][A-Za-z0-9_]*)(?:\s*=\s*(?P<value>-?\d+))?,?$")


def parse_enum(path: Path) -> dict[str, int]:
    text = path.read_text(encoding="utf-8-sig")
    body = text.split("{", 1)[1].rsplit("}", 1)[0]
    result: dict[str, int] = {}
    value = -1
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("["):
            continue
        match = MEMBER.fullmatch(line)
        if not match:
            raise ValueError(f"Unsupported enum line in {path}: {line}")
        value = int(match.group("value")) if match.group("value") is not None else value + 1
        result[match.group("name")] = value
    if not result:
        raise ValueError(f"No enum values found in {path}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("enum_sources", nargs="+", type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
    assembly = next(
        record
        for record in manifest["core_keeper"]["assembly_manifest"]
        if record["path"].endswith("/Pug.Base.dll")
    )
    enums = {source.stem: parse_enum(source) for source in args.enum_sources}
    result = {
        "schema_version": 1,
        "core_keeper_steam_build_id": manifest["core_keeper"]["steam_build_id"],
        "source_assembly": assembly,
        "enums": enums,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
