"""Verify generated focused playtest archives against the canonical catalog."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path


GROUPS = (
    "critters",
    "goldensanity",
    "cardsanity",
    "blocksanity",
    "fishsanity",
    "skillsanity",
    "figurinesanity",
    "valuablesanity",
    "toolsanity",
    "weaponsanity",
    "accessanity",
    "jewelrysanity",
    "armorsanity",
    "petsanity",
    "merchantsanity",
)


def spoiler_locations(archive: Path) -> set[str]:
    with zipfile.ZipFile(archive) as package:
        spoiler_name = next(name for name in package.namelist() if name.endswith("_Spoiler.txt"))
        spoiler = package.read(spoiler_name).decode("utf-8-sig")
    return {
        match.group(1).strip()
        for line in spoiler.splitlines()
        if (match := re.match(r"^([^ ].*?):\s+.+$", line))
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    catalog = json.loads((args.root / "data" / "canonical_catalog.json").read_text(encoding="utf-8"))
    room_manifest = json.loads(
        (args.root / "playtest" / "focused_rooms.json").read_text(encoding="utf-8")
    )
    room_records = {row["group"]: row for row in room_manifest["rooms"]}
    optional_names = {
        row["display_name"]
        for row in catalog["checks"]
        if row["group"] in GROUPS
    }
    for group in GROUPS:
        expected = {
            row["display_name"]
            for row in catalog["checks"]
            if row["group"] == group and row["goal_scope"] == "lower_wall"
        }
        room = args.root / "dist" / f"playtest-room-{group}"
        archives = list(room.glob("AP_*.zip"))
        if len(archives) != 1:
            raise SystemExit(f"{group}: expected one room archive, found {len(archives)}")
        actual = spoiler_locations(archives[0]) & optional_names
        if actual != expected:
            raise SystemExit(
                f"{group}: focused locations differ; missing={sorted(expected - actual)}, "
                f"unexpected={sorted(actual - expected)}"
            )
        record = room_records[group]
        if archives[0].name != record["archive"]:
            raise SystemExit(f"{group}: archive name differs from focused room manifest")
        if len(actual) != record["check_count"]:
            raise SystemExit(f"{group}: check count differs from focused room manifest")
        digest = hashlib.sha256(archives[0].read_bytes()).hexdigest()
        if digest != record["sha256"]:
            raise SystemExit(f"{group}: archive hash differs from focused room manifest")
        print(f"{group}: {len(actual)} focused Lower Wall checks verified ({archives[0].name})")


if __name__ == "__main__":
    main()
