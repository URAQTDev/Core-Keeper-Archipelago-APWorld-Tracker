"""Resolve a check group to exact current-game sprites by normalized pixel identity."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from PIL import Image


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


def digest(image: Image.Image) -> str:
    return hashlib.sha256(normalize(image).tobytes()).hexdigest()


def snake(value: str) -> str:
    return re.sub(
        r"[^a-z0-9]+", "_", re.sub(r"(?<!^)(?=[A-Z])", "_", value).lower()
    ).strip("_")


def reference_path(row: dict, manifest: dict[str, str]) -> str:
    name = row["display_name"]
    if name in manifest:
        return manifest[name]
    if name.startswith("Hatch "):
        collected_name = "Collect " + name.removeprefix("Hatch ")
        if collected_name in manifest:
            return manifest[collected_name]
    raise KeyError(f"No reference icon for {name}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("game_root", type=Path)
    parser.add_argument("candidates", type=Path)
    parser.add_argument("reference_manifest", type=Path)
    parser.add_argument("reference_root", type=Path)
    parser.add_argument("group")
    parser.add_argument("output", type=Path)
    parser.add_argument("--unitypy", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.unitypy))
    import UnityPy

    candidates = [
        row
        for row in json.loads(args.candidates.read_text(encoding="utf-8"))["checks"]
        if row["group"] == args.group
    ]
    reference_manifest = json.loads(args.reference_manifest.read_text(encoding="utf-8"))
    wanted = {
        digest(Image.open(args.reference_root / reference_path(row, reference_manifest)))
        for row in candidates
    }
    names_by_digest: dict[str, set[str]] = {key: set() for key in wanted}
    sources = [args.game_root / "CoreKeeper_Data" / "resources.assets"]
    bundle = args.game_root / "CoreKeeper_Data" / "StreamingAssets" / "aa" / "StandaloneWindows64" / "defaultlocalgroup_assets_all.bundle"
    if bundle.is_file():
        sources.append(bundle)
    for source in sources:
        environment = UnityPy.load(str(source))
        for obj in environment.objects:
            if obj.type.name not in {"Sprite", "Texture2D"}:
                continue
            asset = obj.read()
            try:
                key = digest(asset.image)
            except (FileNotFoundError, PermissionError, ValueError):
                continue
            if key in names_by_digest:
                names_by_digest[key].add(asset.m_Name)
    missing = sorted(key for key, names in names_by_digest.items() if not names)
    if missing:
        raise SystemExit(f"No exact current-game match for {len(missing)} reference hashes")
    generated = {
        snake(row["display_name"]): sorted(
            names_by_digest[digest(Image.open(args.reference_root / reference_path(row, reference_manifest)))]
        )[0]
        for row in candidates
    }
    existing = json.loads(args.output.read_text(encoding="utf-8")) if args.output.is_file() else {}
    existing.update(generated)
    args.output.write_text(
        json.dumps(dict(sorted(existing.items())), indent=2) + "\n", encoding="utf-8"
    )
    print(f"Mapped {len(generated)} {args.group} checks to exact current-game sprites.")


if __name__ == "__main__":
    main()
