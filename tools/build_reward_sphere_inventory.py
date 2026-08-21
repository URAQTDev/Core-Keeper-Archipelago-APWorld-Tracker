from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ITEMS_PATH = ROOT / "apworld" / "core_keeper" / "items.py"
OUTPUT_PATH = ROOT / "REWARD_SPHERE_INVENTORY.md"


tree = ast.parse(ITEMS_PATH.read_text(encoding="utf-8"))


def assigned_dict(name: str) -> ast.Dict:
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in node.targets
        ):
            assert isinstance(node.value, ast.Dict)
            return node.value
    raise KeyError(name)


id_node = assigned_dict("ITEM_NAME_TO_ID")
item_ids = {
    ast.literal_eval(key): ast.literal_eval(value)
    for key, value in zip(id_node.keys, id_node.values)
}

classification_node = assigned_dict("ITEM_CLASSIFICATIONS")
classifications: dict[str, str] = {}
for key, value in zip(classification_node.keys, classification_node.values):
    item_name = ast.literal_eval(key)
    if isinstance(value, ast.Attribute):
        classifications[item_name] = value.attr
    else:
        classifications[item_name] = ast.unparse(value)


equipment_options = {
    "reward_tools": "Tools reward toggle",
    "reward_weapons": "Weapons reward toggle",
    "reward_jewelry": "Jewelry reward toggle",
    "reward_accessories": "Accessories reward toggle",
    "reward_armor": "Armor reward toggle",
}
equipment: dict[str, str] = {}
create_items = next(
    node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "create_items"
)
for node in ast.walk(create_items):
    if not isinstance(node, ast.If) or not isinstance(node.test, ast.Attribute):
        continue
    option = node.test.attr
    if option not in equipment_options:
        continue
    for child in ast.walk(node):
        if not isinstance(child, ast.Call) or not isinstance(child.func, ast.Attribute):
            continue
        if child.func.attr != "extend" or not child.args or not isinstance(child.args[0], ast.List):
            continue
        for element in child.args[0].elts:
            equipment[ast.literal_eval(element)] = equipment_options[option]


license_counts = {
    "Progressive Workbench License": (7, "Licenses: Workbench and Anvil or higher"),
    "Progressive Anvil License": (7, "Licenses: Workbench and Anvil or higher"),
    "Progressive Furnace License": (3, "Licenses: Important Crafting or higher"),
    "Progressive Automation Table License": (2, "Licenses: All"),
    "Progressive Alchemy Table License": (2, "Licenses: All"),
    "Progressive Jewelry Workbench License": (2, "Licenses: All"),
    "Pouch Workbench License": (1, "Licenses: All"),
    "Boat Workbench License": (1, "Licenses: Important Crafting or higher"),
    "Fishing Workbench License": (1, "Licenses: Important Crafting or higher"),
    "Egg Incubator License": (1, "Licenses: Important Crafting or higher"),
    "Key Casting Table License": (1, "Licenses: Important Crafting or higher"),
    "Salvage and Repair Station License": (1, "Licenses: Important Crafting or higher"),
    "Ancient Hologram Pod License": (1, "Licenses: Important Crafting or higher"),
    "Table Saw License": (1, "Licenses: Important Crafting or higher"),
    "Cooking Pot License": (1, "Licenses: Important Crafting or higher"),
    "Carpenter's Table License": (1, "Licenses: All"),
    "Distillery Table License": (1, "Licenses: All"),
    "Electronics Table License": (1, "Licenses: All"),
    "Railway Forge License": (1, "Licenses: All"),
    "Go-Kart Workbench License": (1, "Licenses: All"),
    "Loom License": (1, "Licenses: All"),
    "Music Workbench License": (1, "Licenses: All"),
    "Livestock Workbench License": (1, "Licenses: All"),
    "Glass Workbench License": (1, "Licenses: All"),
    "Painter's Table License": (1, "Licenses: All"),
    "Progressive Smithing Table License": (2, "Licenses: All"),
    "Glass Smelter License": (1, "Licenses: All"),
    "Rift Statue License": (1, "Licenses: All"),
    "Upgrade Station License": (1, "Licenses: All"),
}

skill_rewards = {
    name: (5, "Skill Points reward toggle")
    for name in item_ids
    if name.startswith("+5 ") and name.endswith(" Skill Points")
}

cache_policy = json.loads((ROOT / "data" / "reward_cache_policy.json").read_text(encoding="utf-8"))
cache_names = {entry["item_name"] for entry in cache_policy["caches"]}
cache_names.add("Empty Cache")


def reward_record(name: str) -> dict[str, object]:
    if name in license_counts:
        copies, enabled = license_counts[name]
        placement = (
            "Early reachable location requested (not biome/sub-sphere constrained)"
            if name == "Salvage and Repair Station License"
            else "Seed-generated logic sphere; no additional placement constraint"
        )
        return {"category": "Licenses", "copies": str(copies), "enabled": enabled, "placement": placement}
    if name in skill_rewards:
        copies, enabled = skill_rewards[name]
        return {"category": "Skill Points", "copies": str(copies), "enabled": enabled,
                "placement": "Seed-generated logic sphere; no additional placement constraint"}
    if name in {
        "Soul Seeker Cache", "Titan Breath Cache", "Phantom Spark Cache",
        "Rune Song Cache", "Credence of Ruin Cache", "Stormbringer Cache",
    }:
        return {"category": "Legendary Caches", "copies": "1",
                "enabled": f"{name} toggle",
                "placement": "Seed-generated location sphere; useful item does not drive restrictive fill"}
    if name in cache_names:
        return {"category": "Weighted Caches", "copies": "Variable; may repeat",
                "enabled": "Corresponding cache weight (forced blank slots use Empty Cache regardless of weight)",
                "placement": "Seed-generated location sphere; filler item does not drive restrictive fill"}
    if name in equipment:
        return {"category": equipment[name], "copies": "At most 1",
                "enabled": equipment[name],
                "placement": "Seed-generated location sphere; filler item does not drive restrictive fill"}
    return {"category": "Not currently inserted", "copies": "0",
            "enabled": "No current item-pool route",
            "placement": "Not placed"}


records = []
for name, item_id in item_ids.items():
    record = reward_record(name)
    record.update(name=name, id=item_id, classification=classifications[name])
    records.append(record)

placed = [record for record in records if record["category"] != "Not currently inserted"]
not_inserted = [record for record in records if record["category"] == "Not currently inserted"]

lines = [
    "# Core Keeper reward sphere inventory",
    "",
    "Generated from `apworld/core_keeper/items.py`, `data/license_policy.json`, and "
    "`data/reward_cache_policy.json`.",
    "",
    "Archipelago computes logical spheres for every generated seed by repeatedly collecting all "
    "currently reachable locations; each reward belongs to the sphere of the location containing it. "
    "Progression rewards participate in restrictive fill so they cannot form an unreachable chain, "
    "provided every Core Keeper access rule is accurate. Useful and filler rewards still appear in "
    "seed-generated location spheres, but they do not drive progression fill. The optional Early "
    "Salvage and Repair request is an additional placement constraint, not its sphere assignment.",
    "",
    "Exact sphere numbers are seed-specific. This inventory therefore reports classification and "
    "extra placement constraints; a generated spoiler/playthrough is required to list the exact "
    "sphere of each reward for a particular seed.",
    "",
    f"Possible reward types currently inserted by at least one option: **{len(placed)}**",
    f"Registered item types with no current pool insertion route: **{len(not_inserted)}**",
    "",
    "## Placement summary",
    "",
    "| Static placement policy | Reward types |",
    "|---|---:|",
    f"| Early reachable location requested, without biome/sub-sphere constraint | "
    f"{sum(record['name'] == 'Salvage and Repair Station License' for record in placed)} |",
    f"| Seed-generated sphere; no additional placement constraint | {sum(record['name'] != 'Salvage and Repair Station License' for record in placed)} |",
    "",
]

category_order = [
    "Licenses", "Skill Points", "Legendary Caches", "Weighted Caches",
    "Tools reward toggle", "Weapons reward toggle", "Jewelry reward toggle",
    "Accessories reward toggle", "Armor reward toggle", "Not currently inserted",
]
for category in category_order:
    category_records = sorted(
        (record for record in records if record["category"] == category),
        key=lambda record: int(record["id"]),
    )
    if not category_records:
        continue
    lines.extend([
        f"## {category} ({len(category_records)})",
        "",
        "| ID | Reward | Classification | Maximum copies | Enabled by | Sphere / sub-sphere placement |",
        "|---:|---|---|---|---|---|",
    ])
    for record in category_records:
        values = [
            str(record["id"]), str(record["name"]), str(record["classification"]),
            str(record["copies"]), str(record["enabled"]), str(record["placement"]),
        ]
        lines.append("| " + " | ".join(value.replace("|", "\\|") for value in values) + " |")
    lines.append("")

OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Wrote {len(records)} registered items ({len(placed)} possible rewards) to {OUTPUT_PATH}")
