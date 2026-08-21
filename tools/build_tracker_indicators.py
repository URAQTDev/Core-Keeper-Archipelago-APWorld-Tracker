"""Generate uniform outlined PopTracker accessibility indicators."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


SIZES = {"small": 40, "medium": 56, "large": 84, "xl": 112}
COLORS = {
    "red": (255, 45, 70, 255),
    "yellow": (255, 214, 35, 255),
    "green": (25, 220, 85, 255),
    "grey": (155, 155, 155, 255),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    output = args.root / "poptracker" / "images"
    for variant, size in SIZES.items():
        outer = max(6, round(size / 7))
        outline = max(1, round(size / 56))
        right, top = size - 2, 2
        for state, color in COLORS.items():
            image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            image.paste((28, 28, 28, 255), (right - outer, top, right, top + outer))
            image.paste(color, (
                right - outer + outline,
                top + outline,
                right - outline,
                top + outer - outline,
            ))
            image.save(
                output / f"accessibility-indicator-{state}-{variant}.png",
                optimize=True,
            )


if __name__ == "__main__":
    main()
