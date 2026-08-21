"""Build the per-variant check icons used by the PopTracker runtime."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps


SIZES = {"small": 40, "medium": 56, "large": 84, "xl": 112}


def fit_icon(source: Image.Image, canvas_size: int, check_key: str = "") -> Image.Image:
    source = source.convert("RGBA")
    width, height = source.size
    # Normalize every source—native inventory sprites, prototype fallbacks,
    # enemies, and bosses—to one centered group-cell footprint. This avoids
    # source canvas size and pre-enlargement changing apparent tracker scale.
    scale = (canvas_size * 0.9) / max(width, height)
    resized = source.resize(
        (max(1, round(width * scale)), max(1, round(height * scale))),
        Image.Resampling.NEAREST,
    )
    canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    canvas.alpha_composite(
        resized,
        ((canvas_size - resized.width) // 2, (canvas_size - resized.height) // 2),
    )
    return canvas


def build(root: Path, force: bool = False, selected: set[str] | None = None) -> None:
    catalog = json.loads((root / "data" / "canonical_catalog.json").read_text(encoding="utf-8"))
    manifest = json.loads((root / "data" / "tracker_asset_manifest.json").read_text(encoding="utf-8"))
    assets = {entry["check_key"]: entry for entry in manifest["assets"]}
    images = root / "poptracker" / "images"
    for check in catalog["checks"]:
        if selected and check["key"] not in selected:
            continue
        asset = assets[check["key"]]
        stable_id = check["stable_id"]
        for variant, size in SIZES.items():
            # The source manifests retain the prototype's legacy state names:
            # "checked" is the normal full-color artwork and "unchecked" is
            # its grey treatment. Populate the runtime folders by appearance,
            # not by those historical labels. Runtime check state then selects
            # normal/color while incomplete and disabled/grey when complete.
            for state, folder in (("checked", "check-icons"),
                                  ("unchecked", "check-icons-disabled")):
                source = Image.open(images / asset["outputs"][state]["path"])
                output = root / "poptracker" / variant / "images" / folder / f"{stable_id}.png"
                if output.is_file() and not force:
                    continue
                output.parent.mkdir(parents=True, exist_ok=True)
                fit_icon(source, size, check["key"]).save(output, optimize=True)
            source = Image.open(images / asset["outputs"]["checked"]["path"]).convert("RGBA")
            alpha = source.getchannel("A")
            dark = ImageOps.grayscale(source).convert("RGBA")
            dark = ImageEnhance.Brightness(dark).enhance(0.22)
            dark.putalpha(alpha)
            output = root / "poptracker" / variant / "images" / "check-icons-absent" / f"{stable_id}.png"
            output.parent.mkdir(parents=True, exist_ok=True)
            fit_icon(dark, size, check["key"]).save(output, optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--keys", nargs="*", default=[])
    args = parser.parse_args()
    build(args.root, args.force, set(args.keys))


if __name__ == "__main__":
    main()
