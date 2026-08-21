"""Apply the approved August 2026 check-sphere corrections."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "canonical_catalog.json"
TRACKER = ROOT / "poptracker" / "locations" / "locations.json"

LOWER = ["lower_wall"]
AZEOS = ["defeat_azeos"]
OMOROTH = ["defeat_omoroth"]
FIRST_TITANS = ["defeat_azeos", "defeat_omoroth", "defeat_ra_akar"]
DRUIDRA = ["defeat_druidra"]
CRYDRA = ["defeat_crydra"]
PYRDRA = ["defeat_pyrdra"]
COMMANDER = ["defeat_core_commander"]
NIMRUZA = ["defeat_nimruza"]
SAHABAR = ["defeat_sahabar"]


def route(all_of: list[str]) -> dict[str, list[str]]:
    return {"all_of": list(all_of), "any_of": []}


def tracker_rule(tokens: list[str], sequence_break: bool = False) -> str:
    counts = Counter(tokens)
    emitted: set[str] = set()
    parts: list[str] = []
    for token in tokens:
        if token in emitted:
            continue
        emitted.add(token)
        parts.append(f"{token}:{counts[token]}" if counts[token] > 1 else token)
    if sequence_break:
        parts.append("[core_keeper_sequence_break]")
    return ",".join(parts)


def write_catalog(catalog: dict) -> None:
    lines = ["{"]
    entries = list(catalog.items())
    for index, (key, value) in enumerate(entries):
        comma = "," if index + 1 < len(entries) else ""
        if isinstance(value, list):
            lines.append(f'  {json.dumps(key)}: [')
            for record_index, record in enumerate(value):
                suffix = "," if record_index + 1 < len(value) else ""
                compact = json.dumps(record, separators=(",", ":"), ensure_ascii=False)
                lines.append(f"    {compact}{suffix}")
            lines.append(f"  ]{comma}")
        elif isinstance(value, dict):
            rendered = json.dumps(value, indent=2, ensure_ascii=False).splitlines()
            lines.append(f'  {json.dumps(key)}: {rendered[0]}')
            lines.extend(f"  {line}" for line in rendered[1:-1])
            lines.append(f"  {rendered[-1]}{comma}")
        else:
            lines.append(f'  {json.dumps(key)}: {json.dumps(value)}{comma}')
    lines.append("}")
    CATALOG.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    checks = {check["display_name"]: check for check in catalog["checks"]}
    changed: set[str] = set()

    def update(
        name: str,
        *,
        normal: list[str] | None = None,
        sequence_break: list[str] | None | object = ...,
        scope: str | None = None,
        group: str | None = None,
    ) -> None:
        if name not in checks:
            raise RuntimeError(f"Missing corrected check: {name}")
        check = checks[name]
        if normal is not None:
            check["normal"] = route(normal)
        if sequence_break is not ...:
            check["sequence_break"] = None if sequence_break is None else route(sequence_break)
        if scope is not None:
            check["goal_scope"] = scope
        if group is not None:
            check["group"] = group
        changed.add(name)

    for name in ("Collect Wildwarden Mask", "Collect Wildwarden Pauldrons", "Collect Wildwarden Pants"):
        update(name, normal=LOWER, scope="defeat_core_commander")
    for name in ("Collect Hazmat Helm", "Collect Hazmat Suit Jacket", "Collect Hazmat Suit Pants"):
        update(name, normal=FIRST_TITANS, sequence_break=LOWER, scope="defeat_core_commander")

    update("Collect Meadow Block", normal=LOWER, scope="defeat_core_commander")
    update("Defeat Ivy the Poisonous Mass", normal=[*LOWER, "ancient_hologram_pod_license"])
    update("Defeat Morpha the Aquatic Mass", normal=[*LOWER, *AZEOS, "ancient_hologram_pod_license"])
    update("Defeat Igneous the Molten Mass", normal=[*LOWER, *OMOROTH, "ancient_hologram_pod_license"])
    update("Slay Moolin", normal=LOWER, scope="defeat_core_commander")
    update("Slay Bambuck", normal=LOWER, scope="defeat_core_commander")
    update("Collect Moon Pincher", normal=AZEOS, sequence_break=LOWER, scope="defeat_core_commander")
    update("Collect Meadow Milk", normal=LOWER, scope="defeat_core_commander")
    update("Collect Ancient Guardian Necklace", normal=LOWER, scope="defeat_core_commander")
    update("Collect Conch Shell Necklace", normal=AZEOS, sequence_break=LOWER, scope="defeat_core_commander")
    update("Collect Tower Shell Necklace", normal=FIRST_TITANS, sequence_break=LOWER, scope="defeat_core_commander")
    update("Collect Fuzzy Egg", normal=LOWER, scope="defeat_core_commander")
    update("Hatch Pheromoth", normal=LOWER, scope="defeat_core_commander")

    skill_tiers = {
        10: [], 20: [], 30: [], 40: LOWER, 50: AZEOS, 60: OMOROTH,
        70: DRUIDRA, 80: PYRDRA, 90: COMMANDER, 100: NIMRUZA,
    }
    for check in catalog["checks"]:
        if not check["display_name"].startswith("Level "):
            continue
        level = int(check["display_name"].split()[1])
        if level in skill_tiers:
            update(check["display_name"], normal=skill_tiers[level])

    # Azeos is the first check after lowering the wall; licenses remain hard requirements.
    update(
        "Defeat Azeos the Sky Titan",
        normal=["lower_wall", "ancient_hologram_pod_license",
                "progressive_furnace_license", "progressive_furnace_license"],
    )
    update("Collect Morpha's Bubble Backpack", normal=AZEOS)
    update("Collect Scorching Aegis", normal=OMOROTH)
    for name in ("Collect Magma Horn Armor", "Collect Magma Torso Armor", "Collect Magma Shin Armor"):
        update(name, normal=OMOROTH)
    update("Slay Kelple", normal=AZEOS)
    update("Slay Drohmble", normal=OMOROTH)

    for name, requirements in {
        "Collect Green Glowbug": AZEOS,
        "Collect Purple Glowbug": NIMRUZA,
        "Collect Ice Wind": AZEOS,
        "Collect Little Death": OMOROTH,
        "Collect Snoot Fly": FIRST_TITANS,
        "Collect Shadow Newt": FIRST_TITANS,
        "Collect Gem Snail": FIRST_TITANS,
        "Collect Manyleg": OMOROTH,
    }.items():
        update(name, normal=requirements, scope="defeat_core_commander" if requirements != NIMRUZA else None)

    for name in ("Slay Bubble Crab", "Slay Tentacle", "Slay Blue Slime", "Slay Caveling Scholar", "Slay Core Sentry"):
        update(name, normal=AZEOS)
    for name in ("Slay Bomb Scarab", "Slay Caveling Assassin", "Slay Caveling Mummy", "Slay Lava Slime", "Slay Lava Butterfly"):
        update(name, normal=OMOROTH)
    for name in ("Slay Mimite", "Slay Orbital Turret", "Slay Nilipede"):
        update(name, normal=FIRST_TITANS)
    update("Slay Crystal Snail", normal=FIRST_TITANS, group="cattle_mutilation")

    update("Collect Carrock", normal=[], scope="lower_wall")
    update("Collect Golden Carrock", normal=[], scope="lower_wall")
    update("Collect Carrock Seed", normal=[], scope="lower_wall")
    update("Collect Morpha's Ring", normal=AZEOS)
    update("Collect Oozy Slippery Egg", normal=[*AZEOS, "ancient_hologram_pod_license"])
    update("Hatch Jr. Blue Slime", normal=[*AZEOS, "ancient_hologram_pod_license", "egg_incubator_license"])
    update("Collect Oozy Lava Egg", normal=[*OMOROTH, "ancient_hologram_pod_license"])
    update("Hatch Jr. Lava Slime", normal=[*OMOROTH, "ancient_hologram_pod_license", "egg_incubator_license"])
    update("Collect Chipped Blade", normal=LOWER, scope="defeat_all_bosses")
    update("Collect Golden Glow Tulip", normal=[], sequence_break=None, scope="lower_wall")

    for name in (
        "Slay Geobot Miner", "Slay Geobot Patroller", "Slay Geobot Scourer",
        "Slay Void Larva Cocoon", "Slay Void Larva", "Slay Void Caveling",
        "Slay Void Caveling Shaman", "Slay Void Caveling Brute",
        "Collect Glowing Mushroom", "Collect Oblidra's Heart", "Collect Brood Void Neuron",
    ):
        update(name, normal=NIMRUZA)
    update("Collect Herald Void Neuron", normal=SAHABAR, scope="defeat_all_bosses")

    write_catalog(catalog)

    tracker_locations = json.loads(TRACKER.read_text(encoding="utf-8"))
    tracker_by_name = {location["name"]: location for location in tracker_locations}
    scope_stage = {
        "lower_wall": 0, "defeat_core_commander": 1,
        "defeat_sahabar": 2, "defeat_all_bosses": 3,
    }
    for name in changed:
        check = checks[name]
        location = tracker_by_name.get(name)
        if location is None:
            raise RuntimeError(f"Missing corrected tracker check: {name}")
        section = location["sections"][0]
        rules: list[str] = []
        if check["normal"]["all_of"]:
            rules.append(tracker_rule(check["normal"]["all_of"]))
        if check["sequence_break"] is not None:
            rules.append(tracker_rule(check["sequence_break"]["all_of"], True))
        if rules:
            section["access_rules"] = rules
        else:
            section.pop("access_rules", None)
        option = f"option_{check['group']}"
        stage = f"goal_stage_{scope_stage[check['goal_scope']]}"
        if check["group"] != "bosses":
            location["visibility_rules"] = [option]
            section["visibility_rules"] = [f"{stage},{option}"]
        else:
            old_visibility = section.get("visibility_rules", [])
            optional = ",option_bosses" if any("option_bosses" in value for value in old_visibility) else ""
            section["visibility_rules"] = [f"{stage}{optional}"]
    TRACKER.write_text(
        json.dumps(tracker_locations, indent=2) + "\n", encoding="utf-8", newline="\n"
    )

    print(f"Applied {len(changed)} canonical and tracker check corrections.")


if __name__ == "__main__":
    main()
