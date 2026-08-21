"""List exact Unity asset names matching one or more case-insensitive terms."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("game_root", type=Path)
    parser.add_argument("terms", nargs="+")
    parser.add_argument("--unitypy", type=Path, required=True)
    args = parser.parse_args()

    sys.path.insert(0, str(args.unitypy))
    import UnityPy

    sources = [args.game_root / "CoreKeeper_Data" / "resources.assets"]
    bundle = (
        args.game_root
        / "CoreKeeper_Data"
        / "StreamingAssets"
        / "aa"
        / "StandaloneWindows64"
        / "defaultlocalgroup_assets_all.bundle"
    )
    if bundle.is_file():
        sources.append(bundle)

    terms = tuple(term.casefold() for term in args.terms)
    matches: set[tuple[str, str, str]] = set()
    for source in sources:
        environment = UnityPy.load(str(source))
        for obj in environment.objects:
            if obj.type.name not in {"Sprite", "Texture2D"}:
                continue
            asset = obj.read()
            name = getattr(asset, "m_Name", "")
            if name and any(term in name.casefold() for term in terms):
                matches.add((name, obj.type.name, source.name))

    for name, object_type, source_name in sorted(matches, key=lambda row: row[0].casefold()):
        print(f"{name}\t{object_type}\t{source_name}")


if __name__ == "__main__":
    main()
