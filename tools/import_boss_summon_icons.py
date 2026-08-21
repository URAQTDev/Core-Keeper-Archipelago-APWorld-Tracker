"""Import exact boss summon-item icons exported from Core Keeper."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps


SLIME_PALETTES = {
    "defeat_glurch": ((45, 18, 70), (225, 65, 10), (255, 190, 25)),
    "defeat_ivy": ((45, 22, 70), (155, 60, 180), (235, 130, 160)),
    "defeat_morpha": ((0, 45, 110), (0, 175, 230), (50, 245, 230)),
    "defeat_igneous": ((24, 24, 29), (62, 61, 66), (116, 111, 108)),
}

SLIME_MIDPOINTS = {}


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


def tint(
    image: Image.Image,
    palette: tuple[
        tuple[int, int, int],
        tuple[int, int, int] | None,
        tuple[int, int, int],
    ],
    midpoint: int = 118,
) -> Image.Image:
    image = image.convert("RGBA")
    alpha = image.getchannel("A")
    luminance = ImageOps.autocontrast(ImageOps.grayscale(image), mask=alpha)
    low, middle, high = palette
    colored = ImageOps.colorize(
        luminance,
        low,
        high,
        mid=middle,
        midpoint=midpoint,
    ).convert("RGBA")
    colored.putalpha(alpha)
    return colored


def tint_igneous(image: Image.Image) -> Image.Image:
    image = image.convert("RGBA")
    alpha = image.getchannel("A")
    luminance = ImageOps.autocontrast(ImageOps.grayscale(image), mask=alpha)

    body = ImageOps.colorize(
        luminance,
        (20, 20, 25),
        (112, 105, 102),
        mid=(55, 52, 56),
        midpoint=120,
    ).convert("RGBA")
    body.putalpha(alpha)

    return body


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

    exported = json.loads((args.export / "manifest.json").read_text(encoding="utf-8"))
    manifest_path = args.root / "data" / "tracker_asset_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    records = {row["check_key"]: row for row in manifest["assets"]}
    image_root = args.root / "poptracker" / "images"

    for check_key, icon in exported.items():
        source = args.export / icon["file"]
        source_payload = source.read_bytes()
        image = Image.open(source)
        if check_key == "defeat_igneous":
            image = tint_igneous(image)
        elif check_key in SLIME_PALETTES:
            image = tint(
                image,
                SLIME_PALETTES[check_key],
                SLIME_MIDPOINTS.get(check_key, 118),
            )
        outputs = {}
        for state, state_image in states(image).items():
            destination = image_root / f"{check_key}_{state}.png"
            state_image.save(destination, "PNG", optimize=True)
            outputs[state] = {
                "path": destination.name,
                "sha256": digest(destination.read_bytes()),
            }
        records[check_key] = {
            "check_key": check_key,
            "sprite_name": icon["sprite_name"],
            "unity_object_type": "ObjectInfo.icon",
            "source": f"local_game_boss_summon/{icon['internal_name']}:0",
            "source_sha256": digest(source_payload),
            "usage_status": (
                "verified_exact_game_summon_icon_slime_tinted"
                if check_key in SLIME_PALETTES
                else "verified_exact_game_summon_icon"
            ),
            "outputs": outputs,
        }

    manifest["assets"] = [records[row["check_key"]] for row in manifest["assets"]]
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Imported {len(exported)} boss summon icons; tinted four shared slime idols.")


if __name__ == "__main__":
    main()
