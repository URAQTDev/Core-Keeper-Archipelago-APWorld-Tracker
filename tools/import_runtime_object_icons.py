"""Build non-combat tracker icons from the player's loaded Core Keeper database."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps


SUPPORTED_TRIGGER_KINDS = {"natural_acquisition", "unlock", "interact"}
MIRROR_KEYS = {"talk_to_brave_merchant", "talk_to_otherworldly_merchant"}
FIXED_COLORED_PET_KEYS = {"hatch_electro_pet", "hatch_arcane_symbiote"}


def apply_gradient(image: Image.Image, palette: list[list[int]]) -> Image.Image:
    image = image.convert("RGBA")
    colors = [tuple(color) for color in palette]
    output = Image.new("RGBA", image.size)
    output.putdata([
        (*colors[round(red * (len(colors) - 1) / 255)], alpha)
        for red, _, _, alpha in image.getdata()
    ])
    return output


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

    catalog = json.loads((args.root / "data" / "canonical_catalog.json").read_text(encoding="utf-8"))
    objects = {row["key"]: row for row in catalog["objects"]}
    exported = json.loads((args.export / "manifest.json").read_text(encoding="utf-8"))
    pet_gradients_path = args.export.parent / "pet-skins" / "selected-gradients.json"
    pet_gradients = json.loads(pet_gradients_path.read_text(encoding="utf-8"))
    exported_by_identity = {
        (int(row["object_id"]), int(row.get("variation", identity.rsplit(":", 1)[1]))): row
        for identity, row in exported.items()
    }
    manifest_path = args.root / "data" / "tracker_asset_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    records = {row["check_key"]: row for row in manifest["assets"]}
    image_root = args.root / "poptracker" / "images"

    imported: list[str] = []
    missing: list[str] = []
    for check in catalog["checks"]:
        trigger = check["trigger"]
        if trigger["kind"] not in SUPPORTED_TRIGGER_KINDS:
            continue
        target_key = trigger.get("target_key")
        obj = objects.get(target_key)
        if obj is None:
            missing.append(f"{check['key']}: unknown target {target_key!r}")
            continue
        variation = int(obj.get("variation", 0))
        icon = exported_by_identity.get((int(obj["object_id"]), variation))
        if icon is None:
            missing.append(f"{check['key']}: {obj['internal_name']}:{variation}")
            continue
        source = args.export / icon["icon_file"]
        if not source.is_file():
            missing.append(f"{check['key']}: missing {source.name}")
            continue
        image = Image.open(source).convert("RGBA")
        if check["key"] in MIRROR_KEYS:
            image = ImageOps.mirror(image)
        if check["key"] in pet_gradients and check["key"] not in FIXED_COLORED_PET_KEYS:
            image = apply_gradient(image, pet_gradients[check["key"]]["palette"])
        outputs = {}
        for state, image in states(image).items():
            destination = image_root / f"{check['key']}_{state}.png"
            image.save(destination, "PNG", optimize=True)
            outputs[state] = {"path": destination.name, "sha256": sha256(destination)}
        records[check["key"]] = {
            "check_key": check["key"],
            "sprite_name": icon["icon_sprite_name"],
            "unity_object_type": "ObjectInfo.icon",
            "source": f"local_game_object_icon/{obj['internal_name']}:{variation}",
            "source_sha256": sha256(source),
            "usage_status": (
                "verified_exact_local_game_pet_skin_gradient"
                if check["key"] in pet_gradients and check["key"] not in FIXED_COLORED_PET_KEYS
                else "verified_exact_local_game_object_icon"
            ),
            "outputs": outputs,
        }
        imported.append(check["key"])

    if missing:
        raise SystemExit("Missing local-game object icons:\n" + "\n".join(missing))
    # Rebuild from the canonical active catalog so removed checks cannot leave
    # legacy game textures in the generated tracker pack.
    manifest["assets"] = [records[row["key"]] for row in catalog["checks"]]
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Imported {len(imported)} non-combat icons from the local game database.")


if __name__ == "__main__":
    main()
