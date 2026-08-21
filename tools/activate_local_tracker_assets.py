"""Switch a fallback tracker template to generated per-check local artwork."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    catalog = json.loads((args.root / "data/canonical_catalog.json").read_text(encoding="utf-8"))
    stable_ids = {check["key"]: int(check["stable_id"]) for check in catalog["checks"]}
    path = args.root / "poptracker/items/checks.json"
    items = json.loads(path.read_text(encoding="utf-8"))
    for item in items:
        stable_id = stable_ids[item["codes"]]
        item["img"] = f"images/check-icons/{stable_id}.png"
        item["disabled_img"] = f"images/check-icons-disabled/{stable_id}.png"
    path.write_text(json.dumps(items, separators=(",", ":")) + "\n", encoding="utf-8")

    manifest_path = args.root / "poptracker/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    version = manifest["package_version"]
    manifest["name"] = f"(Textured) Core Keeper Archipelago Mainline {version}"
    for variant in manifest.get("variants", {}).values():
        display_name = variant.get("display_name", "Core Keeper Mainline")
        if not display_name.startswith("(Textured) "):
            variant["display_name"] = f"(Textured) {display_name} {version}"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    (args.root / "poptracker/scripts/asset_mode.lua").write_text(
        "CK_LOCAL_TEXTURES_ACTIVE = true\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
