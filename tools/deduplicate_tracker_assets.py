"""Collapse byte-identical rendered tracker states onto one canonical PNG."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()

    manifest_path = args.root / "data/tracker_asset_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    images = args.root / "poptracker/images"
    canonical_by_hash: dict[str, str] = {}
    referenced: set[str] = set()

    for entry in manifest["assets"]:
        for state in ("checked", "unchecked", "unavailable"):
            output = entry["outputs"][state]
            digest = output["sha256"]
            canonical = canonical_by_hash.setdefault(digest, output["path"])
            output["path"] = canonical
            referenced.add(canonical)

    for image in images.glob("*.png"):
        if image.name == "transparent.png" or image.name.startswith("accessibility-indicator-"):
            continue
        if image.name not in referenced:
            image.unlink()

    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Deduplicated tracker artwork to {len(canonical_by_hash)} rendered PNGs.")


if __name__ == "__main__":
    main()
