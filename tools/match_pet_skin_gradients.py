"""Identify exact Core Keeper pet gradient maps against validated rendered icons."""

import argparse
import json
from pathlib import Path
from PIL import Image, ImageOps


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("export", type=Path)
    parser.add_argument("reference", type=Path)
    args = parser.parse_args()
    data = json.loads((args.export / "pet-skins/manifest.json").read_text())
    gradients = [
        [tuple(int(color[channel]) for channel in ("r", "g", "b")) for color in row.get("array", [])]
        for row in data
        if row.get("$type") == "GradientMapDataBlock" and len(row.get("array", [])) > 1
    ]
    catalog = json.loads((args.root / "data/canonical_catalog.json").read_text())
    objects = {row["key"]: row for row in catalog["objects"]}
    icon_manifest = json.loads((args.export / "object-icons/manifest.json").read_text())
    icons = {(int(row["object_id"]), int(row.get("variation", 0))): row for row in icon_manifest.values()}
    matches = {}
    for check in (row for row in catalog["checks"] if row["key"].startswith("hatch_")):
        obj = objects[check["trigger"]["target_key"]]
        icon = icons[(int(obj["object_id"]), 0)]
        source = Image.open(args.export / "object-icons" / icon["icon_file"]).convert("RGBA")
        reference = Image.open(args.reference / f"{check['key']}_checked.png").convert("RGBA")
        reference = reference.resize(source.size, Image.Resampling.NEAREST)
        gray = ImageOps.grayscale(source)
        source_pixels = list(source.getdata())
        gray_pixels = list(gray.getdata())
        reference_pixels = list(reference.getdata())
        best = (float("inf"), -1)
        for index, palette in enumerate(gradients):
            error = count = 0
            for base, shade, target in zip(source_pixels, gray_pixels, reference_pixels):
                if base[3] == 0 or target[3] == 0:
                    continue
                color = palette[round(shade * (len(palette) - 1) / 255)]
                error += sum((color[channel] - target[channel]) ** 2 for channel in range(3))
                count += 3
            score = error / max(1, count)
            if score < best[0]:
                best = (score, index)
        matches[check["key"]] = {"gradient_index": best[1], "score": best[0], "palette": gradients[best[1]]}
        print(check["key"], best[1], round(best[0], 2))
    (args.export / "pet-skins/selected-gradients.json").write_text(json.dumps(matches, indent=2) + "\n")


if __name__ == "__main__":
    main()
