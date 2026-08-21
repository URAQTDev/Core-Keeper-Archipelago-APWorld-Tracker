"""Generate PopTracker check definitions and variant layouts from the catalog."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


VARIANTS = {
    "medium": (48, 8),
    "small": (32, 10),
    "large": (64, 7),
    "xl": (80, 6),
}

IMPORTANT_LICENSES = [
    "progressive_workbench_license", "progressive_anvil_license",
    "progressive_furnace_license", "salvage_and_repair_station_license",
    "cooking_pot_license", "ancient_hologram_pod_license", "table_saw_license",
    "fishing_workbench_license", "egg_incubator_license",
    "key_casting_table_license",
]
OTHER_LICENSES = [
    "progressive_alchemy_table_license", "progressive_jewelry_workbench_license",
    "progressive_automation_table_license", "progressive_smithing_table_license",
    "boat_workbench_license", "electronics_table_license", "pouch_workbench_license",
    "glass_smelter_license",
    "distillery_table_license", "rift_statue_license", "upgrade_station_license",
    "glass_workbench_license", "railway_forge_license", "loom_license",
    "go_kart_workbench_license", "carpenter_s_table_license",
    "livestock_workbench_license", "painter_s_table_license", "music_workbench_license",
]
LICENSES = IMPORTANT_LICENSES + OTHER_LICENSES
SKILL_TABS = [
    ("Mining", "mining"),
    ("Running", "running"),
    ("Melee Combat", "melee_combat"),
    ("Vitality", "vitality"),
    ("Crafting", "crafting"),
    ("Range Combat", "range_combat"),
    ("Gardening", "gardening"),
    ("Fishing", "fishing"),
    ("Cooking", "cooking"),
    ("Magic", "magic"),
    ("Summoning", "summoning"),
    ("Explosives", "explosives"),
]

CHECK_ORDER_OVERRIDES = {
    "food": [
        "collect_mushroom", "collect_giant_mushroom", "collect_heart_berry",
        "collect_glow_tulip", "collect_bomb_pepper", "collect_larva_meat",
        "collect_marbled_meat", "collect_meadow_milk", "collect_amber_larva",
        "collect_carrock", "collect_puffungi", "collect_bloat_oat",
        "collect_dodo_egg", "collect_paradise_fruit_basket", "collect_pewpaya",
        "collect_pinegrapple", "collect_splendid_amalgam", "collect_sunrice",
        "collect_lunacorn", "collect_atlantean_worm_heart",
        "collect_glowing_mushroom", "collect_oblidra_heart",
    ],
    "unique_materials": [
        "collect_crystal_skull_shard", "collect_clear_gemstone", "collect_chipped_blade",
        "collect_shutdown_protocol", "collect_anomaly_report", "collect_overwrite_transcript",
        "collect_channeling_gemstone", "collect_fractured_limbs", "collect_energy_string",
        "collect_pink_hydra_eye", "collect_white_hydra_eye", "collect_coiled_branch",
        "collect_frozen_orb", "collect_magma_rod", "collect_crystal_meteor_shard",
        "collect_oblivion_fragment", "collect_void_forged_barrel",
        "collect_sanctified_firing_core", "collect_sahabar_mortar_housing",
    ],
    "key_items": [
        "collect_glurch_eye", "collect_ghorm_horn", "collect_stolen_crystal_heart",
        "collect_admin_key", "collect_azeos_feather_fan", "collect_omoroth_compass",
        "collect_ra_akar_automaton", "collect_brood_void_neuron", "collect_herald_void_neuron",
    ],
    "refined_materials": [
        "collect_glass_piece", "collect_plank", "collect_coral_wood_plank", "collect_gleam_wood_plank",
        "collect_copper_bar", "collect_tin_bar", "collect_iron_bar", "collect_gold_bar",
        "collect_scarlet_bar", "collect_octarine_bar", "collect_galaxite_bar",
        "collect_solarite_bar", "collect_pandorium_bar", "collect_relucite_bar",
    ],
    "cattle_mutilation": [
        "slay_strolly_poly", "slay_moolin", "slay_bambuck", "slay_kelple",
        "slay_dodo", "slay_drohmble", "slay_crystal_snail",
    ],
}

CHECK_CATEGORIES = [
    ("Default Checks", [
        "raw_materials", "refined_materials", "locked_chests", "seeds", "food",
        "enemies",
    ]),
    ("Optional Checks", [
        "unique_materials", "key_items", "bosses", "merchantsanity", "petsanity",
        "blocksanity", "goldensanity", "critters", "cattle_mutilation",
    ]),
    ("Sanity Checks", [
        "skillsanity", "fishsanity", "figurinesanity", "cardsanity",
        "valuablesanity", "toolsanity", "weaponsanity", "jewelrysanity",
        "accessanity", "armorsanity",
    ]),
]

def lua_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def prototype_ordered_checks(catalog: dict, order: dict) -> list[dict]:
    checks_by_id = {check["stable_id"]: check for check in catalog["checks"]}
    stable_ids = order["stable_ids"]
    if len(stable_ids) != len(set(stable_ids)):
        raise ValueError("Prototype tracker order contains duplicate stable IDs")
    # Keep retired stable IDs in the historical order file so IDs are never
    # silently reused. Newly assigned IDs follow the historical prototype
    # order until a deliberate category override places them elsewhere.
    ordered = [checks_by_id[stable_id] for stable_id in stable_ids if stable_id in checks_by_id]
    new_ids = sorted(set(checks_by_id) - set(stable_ids))
    return ordered + [checks_by_id[stable_id] for stable_id in new_ids]


def render_checks(catalog: dict, asset_manifest: dict, order: dict) -> str:
    assets = {row["check_key"]: row for row in asset_manifest["assets"]}
    rows = ["-- Generated by tools/build_poptracker.py. Do not edit by hand.", "CK_CHECK_DEFINITIONS = {"]
    for check in prototype_ordered_checks(catalog, order):
        icons = assets[check["key"]]["outputs"]
        rows.append(
            "    { code = %s, id = %d, name = %s, icons = { checked = %s, unchecked = %s, unavailable = %s } },"
            % (
                lua_string(check["key"]),
                check["stable_id"],
                lua_string(check["display_name"]),
                lua_string(icons["checked"]["path"]),
                lua_string(icons["unchecked"]["path"]),
                lua_string(icons["unavailable"]["path"]),
            )
        )
    rows.append("}")
    return "\n".join(rows) + "\n"


def render_check_items(catalog: dict, order: dict) -> str:
    items = []
    for check in prototype_ordered_checks(catalog, order):
        stable_id = check["stable_id"]
        items.append({
            "name": check["display_name"],
            "type": "toggle",
            "img": f"images/check-icons/{stable_id}.png",
            "disabled_img": f"images/check-icons-disabled/{stable_id}.png",
            "disabled_img_mods": "none",
            "codes": check["key"],
        })
    return json.dumps(items, ensure_ascii=False, separators=(",", ":")) + "\n"


def render_layout(
    catalog: dict,
    metadata: dict,
    order: dict,
    item_size: int,
    columns: int,
) -> str:
    checks_by_group: dict[str, list[str]] = {}
    for check in prototype_ordered_checks(catalog, order):
        checks_by_group.setdefault(check["group"], []).append(check["key"])
    raw = checks_by_group["raw_materials"]
    raw.remove("collect_pandorium_ore")
    raw.insert(raw.index("collect_desert_ruby") + 1, "collect_pandorium_ore")
    for group, codes in CHECK_ORDER_OVERRIDES.items():
        if set(checks_by_group[group]) != set(codes):
            raise ValueError(f"Check order override mismatch for {group}")
        checks_by_group[group] = codes
    display = {group["key"]: group["display_name"] for group in metadata["groups"]}
    ordered_groups = [group["key"] for group in metadata["groups"] if group["key"] in checks_by_group]
    tabs = []
    tabs.append({
        "title": "Licenses",
        "content": {
            "type": "array",
            "orientation": "horizontal",
            "background": "#151515",
            "margin": 0,
            "content": [
                {"type": "text", "text": ""},
                {"type": "itemgrid", "background": "#151515",
                 "h_alignment": "center", "v_alignment": "top",
                 "item_size": item_size, "item_margin": 2,
                 "rows": [LICENSES[index:index + max(1, round(len(LICENSES) ** 0.5))]
                          for index in range(
                              0, len(LICENSES), max(1, round(len(LICENSES) ** 0.5))
                          )]},
                {"type": "text", "text": ""},
            ],
        },
    })
    group_tabs = {}
    for group in ordered_groups:
        codes = checks_by_group[group]
        if group == "skillsanity":
            skill_pages = []
            for title, suffix in SKILL_TABS:
                skill_codes = [f"level_{level}_{suffix}" for level in range(10, 101, 10)]
                if not set(skill_codes) <= set(codes):
                    raise ValueError(f"Missing Skillsanity checks for {title}")
                grid = {
                    "type": "itemgrid", "background": "#151515",
                    "h_alignment": "center", "v_alignment": "top",
                    "item_size": item_size, "item_margin": 2,
                    "rows": [skill_codes[index:index + min(columns, 5)]
                             for index in range(0, len(skill_codes), min(columns, 5))],
                }
                skill_pages.append({
                    "title": title,
                    "content": {"type": "array", "orientation": "horizontal",
                                "background": "#151515", "margin": 0,
                                "content": [{"type": "text", "text": ""}, grid,
                                            {"type": "text", "text": ""}]},
                })
            group_tabs[group] = {
                "title": display[group],
                "content": {"type": "tabbed", "background": "#151515", "tabs": skill_pages},
            }
            continue
        page_capacity = columns * columns
        page_codes = [
            codes[index:index + page_capacity]
            for index in range(0, len(codes), page_capacity)
        ]
        page_contents = []
        for page in page_codes:
            side = min(columns, max(1, round(len(page) ** 0.5)))
            grid = {
                "type": "itemgrid",
                "background": "#151515",
                "h_alignment": "center",
                "v_alignment": "top",
                "item_size": item_size,
                "item_margin": 2,
                "rows": [
                    page[index:index + side]
                    for index in range(0, len(page), side)
                ],
            }
            page_contents.append({
                "type": "array",
                "orientation": "horizontal",
                "background": "#151515",
                "margin": 0,
                "content": [
                    {"type": "text", "text": ""},
                    grid,
                    {"type": "text", "text": ""},
                ],
            })
        content = page_contents[0] if len(page_contents) == 1 else {
            "type": "tabbed",
            "background": "#151515",
            "tabs": [
                {"title": str(index + 1), "content": page}
                for index, page in enumerate(page_contents)
            ],
        }
        group_tabs[group] = {"title": display[group], "content": content}
    categorized_groups = [group for _, groups in CHECK_CATEGORIES for group in groups]
    if categorized_groups != ordered_groups:
        raise ValueError("Tracker check categories do not match check metadata order")
    tabs.extend(group_tabs[group] for _, groups in CHECK_CATEGORIES for group in groups)
    result = {
        "tracker_default": {
            "type": "dock",
            "background": "#151515",
            "content": {"type": "tabbed", "tabs": tabs},
        }
    }
    return json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n"


def outputs(root: Path) -> dict[Path, str]:
    catalog = json.loads((root / "data" / "canonical_catalog.json").read_text(encoding="utf-8"))
    metadata = json.loads((root / "data" / "check_group_metadata.json").read_text(encoding="utf-8"))
    assets = json.loads((root / "data" / "tracker_asset_manifest.json").read_text(encoding="utf-8"))
    order = json.loads((root / "data" / "prototype_tracker_order.json").read_text(encoding="utf-8"))
    logic_items = json.loads((root / "poptracker" / "items" / "logic.json").read_text(encoding="utf-8"))
    available_license_codes = {
        item["codes"] for item in logic_items
        if "license" in str(item.get("codes", ""))
    }
    ordered_license_codes = set(LICENSES)
    if available_license_codes != ordered_license_codes:
        raise ValueError("Prototype license order does not match the available license items")
    license_items = {
        item["codes"]: item for item in logic_items
        if item.get("codes") in ordered_license_codes
    }
    first_license = next(
        index for index, item in enumerate(logic_items)
        if item.get("codes") in ordered_license_codes
    )
    nonlicenses = [
        item for item in logic_items if item.get("codes") not in ordered_license_codes
    ]
    reordered_logic = (
        nonlicenses[:first_license]
        + [license_items[code] for code in LICENSES]
        + nonlicenses[first_license:]
    )
    active_ids = {check["stable_id"] for check in catalog["checks"]}
    tracker_locations = json.loads(
        (root / "poptracker" / "locations" / "locations.json").read_text(encoding="utf-8")
    )
    tracker_locations = [
        location for location in tracker_locations
        if int(Path(location["chest_unopened_img"]).stem) in active_ids
    ]
    present_names = {location["name"] for location in tracker_locations}
    scope_stages = {
        "lower_wall": 0, "defeat_core_commander": 1,
        "defeat_sahabar": 2, "defeat_all_bosses": 3,
    }
    def tracker_requirements(requirements: list[str]) -> list[str]:
        expanded = []
        for requirement in requirements:
            if requirement == "lower_wall":
                expanded.extend(["defeat_glurch", "defeat_ghorm", "defeat_malugaz"])
            else:
                expanded.append(requirement)
        return expanded
    for check in prototype_ordered_checks(catalog, order):
        if check["display_name"] in present_names:
            continue
        section = {
            "name": "Checked", "item_count": 1,
            "visibility_rules": [
                f"goal_stage_{scope_stages[check['goal_scope']]},option_{check['group']}"
            ],
        }
        access_rules = []
        normal = tracker_requirements(check["normal"]["all_of"])
        if normal:
            access_rules.append(",".join(normal))
        if check["sequence_break"]:
            sequence = tracker_requirements(check["sequence_break"]["all_of"])
            if sequence:
                access_rules.append(",".join(sequence) + ",[core_keeper_sequence_break]")
        if access_rules:
            section["access_rules"] = access_rules
        tracker_locations.append({
            "name": check["display_name"],
            "chest_unopened_img": f"images/check-icons/{check['stable_id']}.png",
            "chest_opened_img": f"images/check-icons-disabled/{check['stable_id']}.png",
            "sections": [section],
            "visibility_rules": [f"option_{check['group']}"],
        })
    location_map = ["return {"] + [
        f'    [{check["stable_id"]}] = {{ {json.dumps(check["display_name"])}, '
        f'"Checked", {json.dumps(check["key"])} }},'
        for check in catalog["checks"]
    ] + ["}"]
    result = {
        root / "poptracker" / "items" / "logic.json": (
            json.dumps(reordered_logic, ensure_ascii=False, indent=2) + "\n"
        ),
        root / "poptracker" / "scripts" / "checks.lua": render_checks(catalog, assets, order),
        root / "poptracker" / "items" / "checks.json": render_check_items(catalog, order),
        root / "poptracker" / "locations" / "locations.json": (
            json.dumps(tracker_locations, ensure_ascii=False, indent=2) + "\n"
        ),
        root / "poptracker" / "scripts" / "location_map.lua": "\n".join(location_map) + "\n",
    }
    for variant, (size, columns) in VARIANTS.items():
        result[root / "poptracker" / variant / "layouts" / "tracker.json"] = render_layout(
            catalog, metadata, order, size, columns
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    stale = []
    for path, content in outputs(args.root).items():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8-sig") != content:
                stale.append(path.relative_to(args.root).as_posix())
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
    if stale:
        raise SystemExit("Stale generated PopTracker files: " + ", ".join(stale))


if __name__ == "__main__":
    main()
