"""Rank extracted game sprites by visual similarity to a reference crop.

This is a discovery aid only. A match is not evidence of game identity; final
assets must still be extracted by name from a source-hashed game bundle.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageChops, ImageStat


def normalized(path: Path, size: int = 64) -> Image.Image:
    image = Image.open(path).convert("RGBA")
    alpha_box = image.getchannel("A").getbbox()
    if alpha_box:
        image = image.crop(alpha_box)
    side = max(image.width, image.height, 1)
    square = Image.new("RGBA", (side, side))
    square.alpha_composite(image, ((side - image.width) // 2, (side - image.height) // 2))
    background = Image.new("RGBA", square.size, (0, 0, 0, 255))
    background.alpha_composite(square)
    return background.convert("RGB").resize((size, size), Image.Resampling.NEAREST)


def rms_difference(left: Image.Image, right: Image.Image) -> float:
    statistics = ImageStat.Stat(ImageChops.difference(left, right))
    return math.sqrt(sum(value * value for value in statistics.rms) / len(statistics.rms))


def ranked_matches(reference: Path, candidates: Path, limit: int) -> list[tuple[float, Path]]:
    target = normalized(reference)
    ranked: list[tuple[float, Path]] = []
    for path in candidates.glob("*.png"):
        try:
            ranked.append((rms_difference(target, normalized(path)), path))
        except (OSError, ValueError):
            continue
    return sorted(ranked, key=lambda row: (row[0], row[1].name.casefold()))[:limit]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("reference", type=Path)
    parser.add_argument("candidates", type=Path)
    parser.add_argument("--limit", type=int, default=12)
    args = parser.parse_args()
    for difference, path in ranked_matches(args.reference, args.candidates, args.limit):
        print(f"{difference:9.4f}  {path.name}")


if __name__ == "__main__":
    main()
