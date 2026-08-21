"""Import the prototype's verified PopTracker access rules into mainline.

The prototype is a specification source only.  Check codes are rewritten to
the canonical mainline keys and check-toggle items are omitted because
mainline supplies isolated LuaItems for those checks.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def rewrite(value, codes: dict[str, str]):
    if isinstance(value, list):
        return [rewrite(entry, codes) for entry in value]
    if isinstance(value, dict):
        return {key: rewrite(entry, codes) for key, entry in value.items()}
    if isinstance(value, str):
        return re.sub(
            r"check_(\d+)",
            lambda match: codes.get(match.group(1), match.group(0)),
            value,
        )
    return value


def normalize_hidden_images(value):
    if isinstance(value, list):
        return [normalize_hidden_images(entry) for entry in value]
    if isinstance(value, dict):
        return {
            key: (
                "images/collect_wood_unavailable.png"
                if key in {"img", "disabled_img"}
                else normalize_hidden_images(entry)
            )
            for key, entry in value.items()
        }
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mainline", type=Path)
    parser.add_argument("prototype", type=Path)
    args = parser.parse_args()

    catalog = json.loads(
        (args.mainline / "data" / "canonical_catalog.json").read_text(encoding="utf-8")
    )
    by_id = {str(row["stable_id"]): row["key"] for row in catalog["checks"]}

    locations = json.loads(
        (args.prototype / "locations" / "locations.json").read_text(encoding="utf-8")
    )
    name_drift = {
        "Collect Dagger Fish": "Collect Dagger Fin",
        "Collect Golden Larva Meat": "Collect Shiny Larva Meat",
        "Collect Litho Triolobite": "Collect Litho Trilobite",
    }
    for location in locations:
        location["name"] = name_drift.get(location["name"], location["name"])
    catalog_names = {row["display_name"] for row in catalog["checks"]}
    prototype_names = {row["name"] for row in locations}
    if not prototype_names <= catalog_names:
        raise SystemExit("Prototype contains locations absent from the canonical catalog")
    scope_stages = {
        "lower_wall": 0,
        "defeat_core_commander": 1,
        "defeat_sahabar": 2,
        "defeat_all_bosses": 3,
    }
    for check in catalog["checks"]:
        if check["display_name"] in prototype_names:
            continue
        section = {
            "name": "Checked",
            "item_count": 1,
            "visibility_rules": [
                f"goal_stage_{scope_stages[check['goal_scope']]},option_{check['group']}"
            ],
        }
        requirements = check["normal"]["all_of"]
        if requirements:
            section["access_rules"] = [",".join(requirements)]
        locations.append({
            "name": check["display_name"],
            "chest_unopened_img": f"images/check-icons/{check['stable_id']}.png",
            "chest_opened_img": f"images/check-icons-disabled/{check['stable_id']}.png",
            "sections": [section],
            "visibility_rules": [f"option_{check['group']}"],
        })
    locations = rewrite(locations, by_id)
    destination = args.mainline / "poptracker" / "locations" / "locations.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(locations, indent=2) + "\n", encoding="utf-8")

    items = json.loads(
        (args.prototype / "items" / "items.json").read_text(encoding="utf-8")
    )
    logic_items = [
        item for item in items
        if not str(item.get("codes", "")).startswith("check_")
    ]
    if not any(item.get("codes") == "option_critters" for item in logic_items):
        logic_items.append({
            "name": "Enable Critters",
            "type": "toggle",
            "img": "images/collect_wood_unavailable.png",
            "codes": "option_critters",
            "initial_active_state": True,
        })
    for index, item in enumerate(logic_items):
        # Licenses are visible tracker controls and retain the prototype's
        # verified station art. Goal and option providers remain hidden and
        # use the tiny placeholder image.
        if "license" not in str(item.get("codes", "")):
            logic_items[index] = normalize_hidden_images(item)
            item = logic_items[index]
        if item.get("name") == "Goal Scope":
            item["codes"] = "goal_scope"
    item_destination = args.mainline / "poptracker" / "items" / "logic.json"
    item_destination.parent.mkdir(parents=True, exist_ok=True)
    item_destination.write_text(json.dumps(logic_items, indent=2) + "\n", encoding="utf-8")

    rows = ["return {"]
    for check in catalog["checks"]:
        rows.append(
            f'    [{check["stable_id"]}] = {{ {json.dumps(check["display_name"])}, '
            f'"Checked", {json.dumps(check["key"])} }},'
        )
    rows.append("}")
    map_destination = args.mainline / "poptracker" / "scripts" / "location_map.lua"
    map_destination.write_text("\n".join(rows) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
