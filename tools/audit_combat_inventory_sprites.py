"""Audit enemy/boss checks for non-figurine inventory-style game sprites."""

from __future__ import annotations

import argparse
import hashlib
import json
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


def digest(image: Image.Image) -> str:
    return hashlib.sha256(normalize(image).tobytes()).hexdigest()


def is_inventory_candidate(name: str) -> bool:
    lowered = name.casefold()
    if "trophy" in lowered or "figurine" in lowered:
        return False
    return any(
        marker in lowered
        for marker in (
            "lootsprite", "creative_mode", "summoningitem", "scanner",
            "hydrabait", "bossmural", "enemy_icon", "pet_electropest",
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("game_root", type=Path)
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--unitypy", type=Path, required=True)
    args = parser.parse_args()

    sys.path.insert(0, str(args.unitypy.resolve()))
    import UnityPy

    catalog = json.loads((args.root / "data" / "canonical_catalog.json").read_text())
    checks = [row for row in catalog["checks"] if row["group"] in {"enemies", "bosses"}]
    references = {
        row["key"]: normalize(
            Image.open(
                args.root.parent / "poptracker" / "core_keeper" / "images"
                / "check-icons" / f"{row['stable_id']}.png"
            )
        )
        for row in checks
    }
    reference_hashes = {key: digest(image) for key, image in references.items()}

    sources = [args.game_root / "CoreKeeper_Data" / "resources.assets"]
    default_bundle = (
        args.game_root / "CoreKeeper_Data" / "StreamingAssets" / "aa"
        / "StandaloneWindows64" / "defaultlocalgroup_assets_all.bundle"
    )
    if default_bundle.is_file():
        sources.append(default_bundle)

    candidates: list[tuple[str, str, str, Image.Image]] = []
    for source in sources:
        environment = UnityPy.load(str(source))
        for obj in environment.objects:
            if obj.type.name != "Sprite":
                continue
            asset = obj.read()
            name = getattr(asset, "m_Name", "")
            if not name or not is_inventory_candidate(name):
                continue
            try:
                candidates.append((name, obj.type.name, source.name, normalize(asset.image)))
            except (FileNotFoundError, PermissionError, ValueError):
                continue

    results = []
    for check in checks:
        key = check["key"]
        ranked = []
        for name, object_type, source, image in candidates:
            score = sum(ImageStat.Stat(ImageChops.difference(references[key], image)).mean)
            ranked.append(
                {
                    "name": name,
                    "object_type": object_type,
                    "source": source,
                    "score": round(score, 3),
                    "exact_visual_match": digest(image) == reference_hashes[key],
                }
            )
        results.append(
            {
                "check_key": key,
                "display_name": check["display_name"],
                "stable_id": check["stable_id"],
                "matches": sorted(ranked, key=lambda row: (row["score"], row["name"]))[:5],
            }
        )

    payload = {
        "schema_version": 1,
        "policy": "non-figurine inventory-style Sprite objects only",
        "candidate_count": len(candidates),
        "checks": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    exact = sum(any(match["exact_visual_match"] for match in row["matches"]) for row in results)
    print(f"Audited {len(results)} combat checks against {len(candidates)} inventory sprites; {exact} exact visual matches.")


if __name__ == "__main__":
    main()
