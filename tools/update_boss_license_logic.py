"""Apply the approved hard boss-license requirements to the canonical catalog."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "canonical_catalog.json"
TRACKER_LOCATIONS = ROOT / "poptracker" / "locations" / "locations.json"

FURNACE_2 = ["progressive_furnace_license"] * 2
FURNACE_3 = ["progressive_furnace_license"] * 3
WORKBENCH_5 = ["progressive_workbench_license"] * 5

RULES = {
    "Defeat Azeos the Sky Titan": {
        "normal": ["lower_wall",
                   "ancient_hologram_pod_license", *FURNACE_2],
        "sequence_break": ["defeat_glurch", "defeat_ghorm", "defeat_malugaz",
                           "ancient_hologram_pod_license", *FURNACE_2],
    },
    "Defeat Omoroth the Sea Titan": {
        "normal": ["defeat_azeos", "ancient_hologram_pod_license",
                   "fishing_workbench_license", *WORKBENCH_5, *FURNACE_2],
        "sequence_break": ["defeat_glurch", "defeat_ghorm", "defeat_malugaz",
                           "ancient_hologram_pod_license", "fishing_workbench_license",
                           *WORKBENCH_5, *FURNACE_2],
    },
    "Defeat Ra-Akar the Sand Titan": {
        "normal": ["defeat_omoroth", "ancient_hologram_pod_license",
                   *FURNACE_3, "table_saw_license"],
        "sequence_break": ["defeat_glurch", "defeat_ghorm", "defeat_malugaz",
                           "ancient_hologram_pod_license", *FURNACE_3,
                           "table_saw_license"],
    },
    "Defeat Druidra the Wild Titan": {
        "normal": ["defeat_azeos", "defeat_omoroth", "defeat_ra_akar",
                   *FURNACE_3, "table_saw_license"],
    },
    "Defeat Crydra the Ice Titan": {
        "normal": ["defeat_druidra", *FURNACE_3, "table_saw_license"],
    },
    "Defeat Pyrdra the Fire Titan": {
        "normal": ["defeat_crydra", *FURNACE_3, "table_saw_license"],
    },
    "Defeat Atlantean Worm": {
        "normal": ["defeat_azeos", "defeat_omoroth", "defeat_ra_akar",
                   "ancient_hologram_pod_license"],
        "sequence_break": ["lower_wall", "ancient_hologram_pod_license"],
    },
    "Defeat Nimruza, Queen of the Burrowed Sands": {
        "normal": ["defeat_core_commander", *FURNACE_3],
        "sequence_break": ["defeat_glurch", "defeat_ghorm", "defeat_malugaz",
                           *FURNACE_3],
    },
}


def tracker_rule(tokens: list[str], *, sequence_break: bool = False) -> str:
    counts = Counter(tokens)
    emitted: set[str] = set()
    parts: list[str] = []
    for token in tokens:
        if token in emitted:
            continue
        emitted.add(token)
        count = counts[token]
        parts.append(f"{token}:{count}" if count > 1 else token)
    if sequence_break:
        parts.append("[core_keeper_sequence_break]")
    return ",".join(parts)


def main() -> None:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    checks = {check["display_name"]: check for check in catalog["checks"]}
    missing = set(RULES) - set(checks)
    if missing:
        raise RuntimeError(f"Missing canonical boss checks: {sorted(missing)}")
    for name, routes in RULES.items():
        check = checks[name]
        for route_name, all_of in routes.items():
            route = check.get(route_name)
            if route is None:
                raise RuntimeError(f"{name} has no {route_name} route")
            route["all_of"] = all_of
    # Preserve the catalog's compact, reviewable one-record-per-line format.
    lines = ["{"]
    top_level = list(catalog.items())
    for index, (key, value) in enumerate(top_level):
        comma = "," if index + 1 < len(top_level) else ""
        if isinstance(value, list):
            lines.append(f'  {json.dumps(key)}: [')
            for record_index, record in enumerate(value):
                record_comma = "," if record_index + 1 < len(value) else ""
                compact = json.dumps(record, separators=(",", ":"), ensure_ascii=False)
                lines.append(f"    {compact}{record_comma}")
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

    tracker_locations = json.loads(TRACKER_LOCATIONS.read_text(encoding="utf-8"))
    tracker_by_name = {location["name"]: location for location in tracker_locations}
    for name, routes in RULES.items():
        location = tracker_by_name.get(name)
        if location is None:
            raise RuntimeError(f"Missing tracker boss location: {name}")
        access_rules = [tracker_rule(routes["normal"])]
        if "sequence_break" in routes:
            access_rules.append(tracker_rule(routes["sequence_break"], sequence_break=True))
        location["sections"][0]["access_rules"] = access_rules
    TRACKER_LOCATIONS.write_text(
        json.dumps(tracker_locations, indent=2) + "\n", encoding="utf-8", newline="\n"
    )


if __name__ == "__main__":
    main()
