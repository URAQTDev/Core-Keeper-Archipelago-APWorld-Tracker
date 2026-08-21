"""Stage the texture-free tracker template and local setup payload."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps


RECIPE_TOOLS = (
    "activate_local_tracker_assets.py",
    "select_pet_skin_gradients.py",
    "import_runtime_object_icons.py",
    "import_creature_loot_sprites.py",
    "import_boss_summon_icons.py",
    "import_runtime_skill_icons.py",
    "import_runtime_license_icons.py",
    "deduplicate_tracker_assets.py",
    "build_tracker_variant_icons.py",
    "build_tracker_indicators.py",
    "package_poptracker.py",
)

SIZES = {"small": 40, "medium": 56, "large": 84, "xl": 112}


def fit(source: Image.Image, size: int) -> Image.Image:
    image = source.convert("RGBA")
    bounds = image.getchannel("A").getbbox()
    if bounds:
        image = image.crop(bounds)
    scale = size * 0.88 / max(image.size)
    image = image.resize(
        (max(1, round(image.width * scale)), max(1, round(image.height * scale))),
        Image.Resampling.LANCZOS,
    )
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.alpha_composite(image, ((size - image.width) // 2, (size - image.height) // 2))
    return canvas


def fallback_states(source: Image.Image, size: int) -> dict[str, Image.Image]:
    colored = fit(source, size)
    alpha = colored.getchannel("A")
    grey = ImageOps.grayscale(colored).convert("RGBA")
    grey.putalpha(alpha)
    return {
        "check-icons": colored,
        "check-icons-disabled": ImageEnhance.Brightness(grey).enhance(0.62),
        "check-icons-absent": ImageEnhance.Brightness(grey).enhance(0.22),
    }


def generate_fallbacks(root: Path, template: Path) -> int:
    logo = Image.open(root / "client/Assets/ArchipelagoLogo.png").convert("RGBA")
    written = 0
    for variant, size in SIZES.items():
        destination = template / "poptracker" / variant / "images"
        destination.mkdir(parents=True, exist_ok=True)
        state_names = {
            "check-icons": "fallback-icon.png",
            "check-icons-disabled": "fallback-icon-disabled.png",
            "check-icons-absent": "fallback-icon-absent.png",
        }
        for state, image in fallback_states(logo, size).items():
            image.save(destination / state_names[state], optimize=True)
            written += 1

    checks_path = template / "poptracker/items/checks.json"
    checks = json.loads(checks_path.read_text(encoding="utf-8"))
    for item in checks:
        item["img"] = "images/fallback-icon.png"
        item["disabled_img"] = "images/fallback-icon-disabled.png"
    checks_path.write_text(json.dumps(checks, separators=(",", ":")) + "\n", encoding="utf-8")
    (template / "poptracker/scripts/asset_mode.lua").write_text(
        "CK_LOCAL_TEXTURES_ACTIVE = false\n", encoding="utf-8"
    )

    logic = json.loads((template / "poptracker/items/logic.json").read_text(encoding="utf-8"))
    license_paths: set[str] = set()
    for item in logic:
        path = item.get("img")
        if path and ("license-icons/" in path or "license-stages/" in path):
            license_paths.add(path)
        for stage in item.get("stages", []):
            path = stage.get("img")
            if path and ("license-icons/" in path or "license-stages/" in path):
                license_paths.add(path)
    license_image = fit(logo, 84)
    for relative in license_paths:
        destination = template / "poptracker" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        license_image.save(destination, optimize=True)
        written += 1

    # Goal and option controls share this canonical unavailable image.
    control = fit(logo, 84)
    control = ImageEnhance.Brightness(ImageOps.grayscale(control).convert("RGBA")).enhance(0.35)
    control.putalpha(fit(logo, 84).getchannel("A"))
    control.save(template / "poptracker/images/collect_wood_unavailable.png", optimize=True)
    return written + 1


def build(root: Path, output: Path) -> None:
    if output.exists():
        shutil.rmtree(output)
    template = output / "template"
    shutil.copytree(root / "poptracker", template / "poptracker")
    shutil.copytree(root / "extractor-output/CoreKeeperArchipelagoExtractor",
                    output / "extractor/CoreKeeperArchipelagoExtractor")
    (template / "data").mkdir(parents=True)
    for name in ("canonical_catalog.json", "license_policy.json", "tracker_asset_manifest.json"):
        shutil.copy2(root / "data" / name, template / "data" / name)
    (output / "tools").mkdir(parents=True)
    for name in RECIPE_TOOLS:
        shutil.copy2(root / "tools" / name, output / "tools" / name)

    # Remove every Core Keeper-derived PNG. Keep only our transparent utility
    # and generated accessibility indicators in the public template.
    keep = {"transparent.png"}
    keep.update(
        f"accessibility-indicator-{state}-{variant}.png"
        for state in ("red", "yellow", "green", "grey")
        for variant in ("small", "medium", "large", "xl")
    )
    for image in (template / "poptracker").rglob("*.png"):
        if image.parent == template / "poptracker/images" and image.name in keep:
            continue
        image.unlink()
    for directory in sorted(
        (path for path in (template / "poptracker").rglob("*") if path.is_dir()),
        key=lambda path: len(path.parts), reverse=True,
    ):
        if not any(directory.iterdir()):
            directory.rmdir()

    fallback_pngs = generate_fallbacks(root, template)
    report = {
        "schema_version": 1,
        "core_keeper_png_count": 0,
        "archipelago_fallback_png_count": fallback_pngs,
        "fallback_source": "client/Assets/ArchipelagoLogo.png (project-owned artwork)",
        "retained_tracker_pngs": sorted(keep),
        "active_checks": len(json.loads(
            (root / "data/canonical_catalog.json").read_text(encoding="utf-8")
        )["checks"]),
    }
    (output / "TEXTURE_FREE_REPORT.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    build(args.root, args.output)


if __name__ == "__main__":
    main()
