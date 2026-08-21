"""Import every creature's exact normal ObjectInfo.icon sprite."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def square(image: Image.Image) -> Image.Image:
    image = image.convert("RGBA")
    bounds = image.getchannel("A").getbbox()
    if bounds:
        image = image.crop(bounds)
    side = max(image.width, image.height)
    result = Image.new("RGBA", (side, side))
    result.alpha_composite(image, ((side - image.width) // 2, (side - image.height) // 2))
    return result


def states(image: Image.Image) -> dict[str, Image.Image]:
    checked = square(image)
    grey = ImageOps.grayscale(checked).convert("RGBA")
    grey.putalpha(checked.getchannel("A"))
    return {
        "checked": checked,
        "unchecked": ImageEnhance.Brightness(grey).enhance(0.62),
        "unavailable": ImageEnhance.Brightness(grey).enhance(0.25),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("export", type=Path)
    args = parser.parse_args()

    catalog = json.loads((args.root / "data" / "canonical_catalog.json").read_text(encoding="utf-8"))
    objects = {row["key"]: row for row in catalog["objects"]}
    exported = json.loads((args.export / "manifest.json").read_text(encoding="utf-8"))
    by_identity = {
        (int(row["object_id"]), int(identity.rsplit(":", 1)[1])): row
        for identity, row in exported.items()
    }
    manifest_path = args.root / "data" / "tracker_asset_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    records = {row["check_key"]: row for row in manifest["assets"]}
    image_root = args.root / "poptracker" / "images"

    imported: list[str] = []
    missing: list[str] = []
    for check in catalog["checks"]:
        if not check["key"].startswith("slay_"):
            continue
        obj = objects[check["trigger"]["target_key"]]
        variation = int(obj.get("variation", 0))
        icon = by_identity.get((int(obj["object_id"]), variation))
        if icon is None:
            missing.append(f"{check['key']} ({obj['internal_name']}:{variation})")
            continue
        sprite_name = str(icon["icon_sprite_name"])
        source_file = icon["icon_file"]
        if not source_file:
            raise SystemExit(f"Missing exported sprite for {check['key']}: {sprite_name}")
        lowered = sprite_name.lower()
        if "trophy" in lowered or "figurine" in lowered:
            raise SystemExit(f"Rejected figurine sprite for {check['key']}: {sprite_name}")
        source = args.export / source_file
        source_payload = source.read_bytes()
        outputs = {}
        for state, image in states(Image.open(source)).items():
            destination = image_root / f"{check['key']}_{state}.png"
            image.save(destination, "PNG", optimize=True)
            outputs[state] = {
                "path": destination.name,
                "sha256": digest(destination.read_bytes()),
            }
        records[check["key"]] = {
            "check_key": check["key"],
            "sprite_name": sprite_name,
            "unity_object_type": "ObjectInfo.icon",
            "source": f"local_game_creature_icon/{obj['internal_name']}:{variation}",
            "source_sha256": digest(source_payload),
            "usage_status": "verified_exact_game_creature_loot_sprite",
            "outputs": outputs,
        }
        imported.append(check["key"])

    if missing:
        raise SystemExit("Missing creature icons:\n" + "\n".join(missing))
    manifest["assets"] = [records[row["check_key"]] for row in manifest["assets"]]
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(
        f"Imported {len(imported)} exact normal ObjectInfo.icon creature sprites."
    )


if __name__ == "__main__":
    main()
