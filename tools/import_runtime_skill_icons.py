"""Generate all skill-level tracker checks from locally exported game sprites."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageOps


SKILLS = {
    "mining": "skill_icons_mining",
    "running": "skill_icons_running",
    "melee_combat": "skill_icons_melee",
    "vitality": "skill_icons_vitality",
    "crafting": "skill_icons_blacksmithing",
    "range_combat": "skill_icons_ranged",
    "gardening": "skill_icons_gardening",
    "fishing": "skill_icons_14",
    "cooking": "skill_icons_16",
    "magic": "skill_icons_magic",
    "summoning": "skill_icons_summoning",
    "explosives": "skill_icons_demolition",
}
SKILL_COLORS = {
    "mining": (249, 225, 83),
    "running": (232, 120, 183),
    "melee_combat": (245, 139, 70),
    "vitality": (242, 90, 105),
    "crafting": (201, 178, 214),
    "range_combat": (94, 224, 162),
    "gardening": (86, 188, 62),
    "fishing": (82, 190, 210),
    "cooking": (201, 151, 125),
    "magic": (37, 139, 221),
    "summoning": (168, 62, 218),
    "explosives": (141, 103, 135),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def square(image: Image.Image) -> Image.Image:
    image = image.convert("RGBA")
    bounds = image.getchannel("A").getbbox()
    if bounds:
        image = image.crop(bounds)
    side = max(image.width, image.height)
    output = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    output.alpha_composite(image, ((side - image.width) // 2, (side - image.height) // 2))
    return output


def add_badge(image: Image.Image, level: int) -> Image.Image:
    output = square(image).resize((48, 48), Image.Resampling.NEAREST)
    label = str(level)
    draw = ImageDraw.Draw(output)
    box = draw.textbbox((0, 0), label)
    width, height = box[2] - box[0], box[3] - box[1]
    x, y = max(0, output.width - width - 2), max(0, output.height - height - 2)
    draw.rectangle((x - 1, y - 1, output.width - 1, output.height - 1), fill=(32, 20, 10, 230))
    draw.text((x, y), label, fill=(255, 225, 65, 255))
    return output


def states(image: Image.Image) -> dict[str, Image.Image]:
    checked = square(image)
    grayscale = ImageOps.grayscale(checked).convert("RGBA")
    grayscale.putalpha(checked.getchannel("A"))
    return {
        "checked": checked,
        "unchecked": ImageEnhance.Brightness(grayscale).enhance(0.62),
        "unavailable": ImageEnhance.Brightness(grayscale).enhance(0.25),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("export", type=Path)
    args = parser.parse_args()

    exported = json.loads((args.export / "manifest.json").read_text(encoding="utf-8"))
    missing_sprites = sorted(set(SKILLS.values()) - set(exported))
    if missing_sprites:
        raise SystemExit("Missing local-game skill sprites: " + ", ".join(missing_sprites))
    catalog = json.loads((args.root / "data" / "canonical_catalog.json").read_text(encoding="utf-8"))
    manifest_path = args.root / "data" / "tracker_asset_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    records = {row["check_key"]: row for row in manifest["assets"]}
    image_root = args.root / "poptracker" / "images"

    imported = 0
    for check in catalog["checks"]:
        if check["trigger"]["kind"] != "skill_level":
            continue
        parts = check["key"].split("_", 2)
        level = int(parts[1])
        skill = parts[2]
        sprite_name = SKILLS[skill]
        source = args.export / exported[sprite_name]
        source_image = Image.open(source).convert("RGBA")
        alpha = source_image.getchannel("A")
        # Core Keeper stores skill art as white masks and applies these colors
        # in its UI. Reapply that game palette before rendering level badges.
        source_image = ImageOps.colorize(
            ImageOps.grayscale(source_image), (0, 0, 0), SKILL_COLORS[skill]
        ).convert("RGBA")
        source_image.putalpha(alpha)
        image = add_badge(source_image, level)
        outputs = {}
        for state, state_image in states(image).items():
            destination = image_root / f"{check['key']}_{state}.png"
            state_image.save(destination, "PNG", optimize=True)
            outputs[state] = {"path": destination.name, "sha256": sha256(destination)}
        records[check["key"]] = {
            "check_key": check["key"],
            "sprite_name": sprite_name,
            "unity_object_type": "Sprite",
            "source": f"local_game_skill_icon/{sprite_name}",
            "source_sha256": sha256(source),
            "usage_status": "generated_from_exact_local_game_skill_sprite",
            "outputs": outputs,
        }
        imported += 1

    manifest["assets"] = [records[row["check_key"]] for row in manifest["assets"]]
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {imported} skill-level icons from twelve local game sprites.")


if __name__ == "__main__":
    main()
