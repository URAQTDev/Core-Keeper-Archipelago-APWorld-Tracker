"""List exact Core Keeper Sprite/Texture2D names matching search terms."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageStat


def normalize(image: Image.Image) -> Image.Image:
    image = image.convert("RGBA")
    box = image.getchannel("A").getbbox()
    if box:
        image = image.crop(box)
    scale = min(64 / image.width, 64 / image.height)
    image = image.resize(
        (max(1, round(image.width * scale)), max(1, round(image.height * scale))),
        Image.Resampling.NEAREST,
    )
    canvas = Image.new("RGBA", (64, 64))
    canvas.alpha_composite(image, ((64 - image.width) // 2, (64 - image.height) // 2))
    return canvas


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("game_root", type=Path)
    parser.add_argument("terms", nargs="+")
    parser.add_argument("--unitypy", type=Path, required=True)
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--references", nargs="*", type=Path, default=[])
    args = parser.parse_args()
    sys.path.insert(0, str(args.unitypy))
    import UnityPy

    sources = [args.game_root / "CoreKeeper_Data" / "resources.assets"]
    bundle = args.game_root / "CoreKeeper_Data" / "StreamingAssets" / "aa" / "StandaloneWindows64" / "defaultlocalgroup_assets_all.bundle"
    if bundle.is_file():
        sources.append(bundle)
    terms = tuple(term.casefold() for term in args.terms)
    names: set[str] = set()
    matches: list[tuple[float, str]] = []
    reference = normalize(Image.open(args.reference)) if args.reference else None
    references = {
        path.stem: normalize(Image.open(path))
        for path in args.references
    }
    multi_matches: dict[str, list[tuple[float, str]]] = {key: [] for key in references}
    for source in sources:
        environment = UnityPy.load(str(source))
        for obj in environment.objects:
            if obj.type.name not in {"Sprite", "Texture2D"}:
                continue
            asset = obj.read()
            name = asset.m_Name
            if any(term in name.casefold() for term in terms):
                names.add(name)
            if (reference is not None or references) and obj.type.name in {"Sprite", "Texture2D"}:
                try:
                    canvas = normalize(asset.image)
                    if reference is not None:
                        score = sum(ImageStat.Stat(ImageChops.difference(reference, canvas)).mean)
                        matches.append((score, name))
                    for key, expected in references.items():
                        score = sum(ImageStat.Stat(ImageChops.difference(expected, canvas)).mean)
                        multi_matches[key].append((score, name))
                except (FileNotFoundError, PermissionError, ValueError):
                    pass
    if reference is not None:
        print("\n".join(f"{score:.3f} {name}" for score, name in sorted(matches)[:20]))
    elif references:
        for key, candidates in multi_matches.items():
            print(f"{key}: " + ", ".join(f"{score:.3f} {name}" for score, name in sorted(candidates)[:3]))
    else:
        print("\n".join(sorted(names, key=str.casefold)))


if __name__ == "__main__":
    main()
