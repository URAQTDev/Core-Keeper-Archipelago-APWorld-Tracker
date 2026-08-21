"""Build license and progressive-stage icons from locally exported stations."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from PIL import Image


def norm(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]", "", value.lower())
    return normalized.replace("basicworkbench", "woodenworkbench")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def square(source: Path) -> Image.Image:
    image = Image.open(source).convert("RGBA")
    bounds = image.getchannel("A").getbbox()
    if bounds:
        image = image.crop(bounds)
    side = max(image.width, image.height)
    output = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    output.alpha_composite(image, ((side - image.width) // 2, (side - image.height) // 2))
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("export_root", type=Path)
    args = parser.parse_args()

    policy = json.loads((args.root / "data" / "license_policy.json").read_text(encoding="utf-8"))
    items = json.loads((args.root / "poptracker" / "items" / "logic.json").read_text(encoding="utf-8"))
    icon_manifest = json.loads((args.export_root / "object-icons" / "manifest.json").read_text(encoding="utf-8"))
    database = json.loads((args.export_root / "runtime_database.raw.json").read_text(encoding="utf-8"))["records"]
    icons_by_id = {int(row["object_id"]): row for row in icon_manifest.values() if int(row.get("variation", 0)) == 0}
    records_by_id = {int(row["object_id"]): row for row in database if int(row.get("variation", 0)) == 0}
    stations_by_license: dict[str, list[dict]] = {}
    for station in policy["stations"]:
        if station["license"]:
            stations_by_license.setdefault(station["license"], []).append(station)

    provenance = []
    for item in items:
        license_name = item.get("name", "")
        stations = stations_by_license.get(license_name)
        if not stations:
            continue
        by_display = {
            norm(str(records_by_id[int(station["object_id"])]["display_name"])): station
            for station in stations
        }
        stage_rows = item.get("stages", [])
        destinations: list[tuple[Path, dict]] = []
        if stage_rows:
            ordered_stations = sorted(stations, key=lambda row: int(row["stage"]))
            if license_name == "Progressive Workbench License":
                ordered_stations.insert(0, next(row for row in policy["stations"] if int(row["object_id"]) == 4003))
            if len(ordered_stations) != len(stage_rows):
                raise SystemExit(f"Stage count mismatch for {license_name}")
            for stage, station in zip(stage_rows, ordered_stations):
                destinations.append((args.root / "poptracker" / stage["img"], station))
            primary_station = destinations[0][1]
        else:
            primary_station = stations[0]
        destinations.append((args.root / "poptracker" / item["img"], primary_station))

        for destination, station in destinations:
            icon = icons_by_id.get(int(station["object_id"]))
            if icon is None:
                raise SystemExit(f"Missing local icon for {station['internal_name']}")
            source = args.export_root / "object-icons" / icon["icon_file"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            square(source).save(destination, "PNG", optimize=True)
            provenance.append({
                "license": license_name,
                "output": destination.relative_to(args.root / "poptracker").as_posix(),
                "object_id": int(station["object_id"]),
                "internal_name": station["internal_name"],
                "sprite_name": icon["icon_sprite_name"],
                "source": f"local_game_object_icon/{station['internal_name']}:0",
                "source_sha256": sha256(source),
                "output_sha256": sha256(destination),
            })

    output = args.root / "data" / "tracker_license_asset_manifest.json"
    output.write_text(json.dumps({"schema_version": 1, "assets": provenance}, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {len(provenance)} license/stage images from local Core Keeper station icons.")


if __name__ == "__main__":
    main()
