"""Extract explicitly named Core Keeper Sprite/Texture2D objects for inspection."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("game_root", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("names", nargs="+")
    parser.add_argument("--unitypy", type=Path, required=True)
    args = parser.parse_args()

    sys.path.insert(0, str(args.unitypy.resolve()))
    import UnityPy

    sources = [args.game_root / "CoreKeeper_Data" / "resources.assets"]
    bundle_root = (
        args.game_root / "CoreKeeper_Data" / "StreamingAssets" / "aa"
        / "StandaloneWindows64"
    )
    default_bundle = bundle_root / "defaultlocalgroup_assets_all.bundle"
    if default_bundle.is_file():
        sources.append(default_bundle)

    wanted = set(args.names)
    found: dict[str, tuple[object, str]] = {}
    for source in sources:
        environment = UnityPy.load(str(source))
        for obj in environment.objects:
            if obj.type.name not in {"Sprite", "Texture2D"}:
                continue
            asset = obj.read()
            if getattr(asset, "m_Name", "") not in wanted:
                continue
            previous = found.get(asset.m_Name)
            if previous is not None and (previous[1] == "Sprite" or obj.type.name != "Sprite"):
                continue
            found[asset.m_Name] = (asset.image.convert("RGBA"), obj.type.name)

    missing = sorted(wanted - found.keys())
    if missing:
        raise SystemExit("Missing named game assets: " + ", ".join(missing))
    args.output.mkdir(parents=True, exist_ok=True)
    for name in sorted(wanted):
        image, object_type = found[name]
        image.save(args.output / f"{name}.{object_type}.png", optimize=True)
    print(f"Extracted {len(found)} named game assets to {args.output}.")


if __name__ == "__main__":
    main()
