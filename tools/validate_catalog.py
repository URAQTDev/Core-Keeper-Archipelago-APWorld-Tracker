"""Validate the reviewed canonical catalog against pinned Core Keeper evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable


KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def walk_hashes(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "sha256" and isinstance(child, str):
                yield child
            else:
                yield from walk_hashes(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_hashes(child)


def unique(records: list[dict[str, Any]], field: str, label: str) -> None:
    values = [record[field] for record in records]
    if len(values) != len(set(values)):
        raise ValueError(f"Duplicate {label} {field}")


def validate_semantics(catalog: dict[str, Any]) -> None:
    objects_by_key = {record["key"]: record for record in catalog["objects"]}
    expected_trigger_kinds = {
        "natural_acquisition": {"item"},
        "kill": {"enemy", "boss"},
        "unlock": {"other"},
        "interact": {"other"},
    }
    for check in catalog["checks"]:
        trigger = check["trigger"]
        trigger_kind = trigger["kind"]
        if trigger_kind == "skill_level":
            continue
        if trigger_kind not in expected_trigger_kinds:
            raise ValueError(f"Check {check['key']} has unsupported trigger kind {trigger_kind!r}")
        target = objects_by_key.get(trigger["target_key"])
        if target is None:
            continue
        if target["kind"] not in expected_trigger_kinds[trigger_kind]:
            raise ValueError(
                f"Check {check['key']} uses {trigger_kind} with {target['kind']} target {target['key']}"
            )

    expected_delivery_kinds = {
        "license": {"station"},
        "object": {"item"},
    }
    for reward in catalog["rewards"]:
        delivery = reward["delivery"]
        delivery_kind = delivery["kind"]
        if delivery_kind in {"cache", "empty"}:
            if delivery.get("target_key") is not None:
                raise ValueError(f"Reward {reward['key']} has a target for {delivery_kind} delivery")
            continue
        if delivery_kind == "skill_points":
            if delivery.get("target_key") not in {
                "mining", "running", "melee", "vitality", "crafting", "range",
                "gardening", "fishing", "cooking", "magic", "summoning", "explosives",
            } or delivery.get("amount") != 5:
                raise ValueError(f"Reward {reward['key']} has invalid skill-point delivery")
            continue
        if delivery_kind not in expected_delivery_kinds:
            raise ValueError(f"Reward {reward['key']} has unsupported delivery kind {delivery_kind!r}")
        target = objects_by_key.get(delivery.get("target_key"))
        if target is None:
            continue
        if target["kind"] not in expected_delivery_kinds[delivery_kind]:
            raise ValueError(
                f"Reward {reward['key']} uses {delivery_kind} with {target['kind']} target {target['key']}"
            )


def validate(catalog_path: Path, game_config_path: Path, manifest_path: Path, source_root: Path) -> None:
    catalog = json.loads(catalog_path.read_text(encoding="utf-8-sig"))
    game_config = json.loads(game_config_path.read_text(encoding="utf-8-sig"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))

    if catalog.get("schema_version") != 1:
        raise ValueError("Unsupported canonical catalog schema_version")
    if catalog["source"]["core_keeper_steam_build_id"] != manifest["core_keeper"]["steam_build_id"]:
        raise ValueError("Catalog Core Keeper build does not match source manifest")
    if catalog["source"]["source_manifest_sha256"] != digest(manifest_path):
        raise ValueError("Catalog source manifest hash is stale")

    objects = catalog["objects"]
    checks = catalog["checks"]
    rewards = catalog["rewards"]
    milestones = catalog["milestones"]
    for records, label in ((objects, "object"), (checks, "check"), (rewards, "reward"), (milestones, "milestone")):
        unique(records, "key", label)
        for record in records:
            if not KEY_PATTERN.fullmatch(record["key"]):
                raise ValueError(f"Invalid {label} key {record['key']!r}")
    seen_object_variations = set()
    for record in objects:
        identity = (record["object_id"], int(record.get("variation", 0)))
        if identity in seen_object_variations:
            raise ValueError("Duplicate object object_id/variation")
        seen_object_variations.add(identity)
    unique(checks, "stable_id", "check")
    unique(rewards, "stable_id", "reward")
    check_ids = {record["stable_id"] for record in checks}
    reward_ids = {record["stable_id"] for record in rewards}
    if check_ids & reward_ids:
        raise ValueError("Item and location stable IDs overlap")
    validate_semantics(catalog)

    game_objects = {
        record["internal_name"]: record["object_id"]
        for record in game_config["object_ids"]["records"]
    }
    for record in objects:
        actual = game_objects.get(record["internal_name"])
        if actual != record["object_id"]:
            raise ValueError(
                f"Object {record['key']} does not match the pinned ObjectID map: "
                f"expected {actual}, catalog has {record['object_id']}"
            )

    object_keys = {record["key"] for record in objects}
    milestone_keys = {record["key"] for record in milestones}
    reward_keys = {record["key"] for record in rewards}
    requirement_keys = object_keys | milestone_keys | reward_keys
    for check in checks:
        if check["trigger"]["kind"] != "skill_level" and check["trigger"]["target_key"] not in object_keys:
            raise ValueError(f"Check {check['key']} has an unknown trigger target")
        requirements = [check["normal"]]
        if check["sequence_break"] is not None:
            requirements.append(check["sequence_break"])
        for requirement in requirements:
            referenced = requirement["all_of"] + [key for route in requirement["any_of"] for key in route]
            unknown = sorted(set(referenced) - requirement_keys)
            if unknown:
                raise ValueError(f"Check {check['key']} references unknown requirements: {unknown}")

    for reward in rewards:
        target = reward["delivery"].get("target_key")
        if (reward["delivery"]["kind"] != "skill_points"
                and target is not None and target not in object_keys):
            raise ValueError(f"Reward {reward['key']} has an unknown delivery target")

    accepted_hashes = set(walk_hashes(manifest))
    accepted_hashes.update(
        digest(source_root / relative)
        for relative in (
            "spec/FEATURE_INVENTORY.md",
            "spec/SKILL_POINTS.md",
            "data/contracts/vertical_slice_hooks.json",
        )
    )
    runtime_database = json.loads(
        (source_root / "data/runtime_database.raw.json").read_text(encoding="utf-8-sig")
    )
    accepted_hashes.add(runtime_database["source"]["normalized_source_sha256"])
    for section in (milestones, objects, checks, rewards):
        for record in section:
            if not record["evidence"]:
                raise ValueError(f"{record['key']} has no evidence")
            for evidence in record["evidence"]:
                value = evidence["sha256"]
                if not SHA256_PATTERN.fullmatch(value) or value not in accepted_hashes:
                    raise ValueError(f"{record['key']} cites an unrecognized evidence hash")
                if evidence["status"] != "verified":
                    raise ValueError(f"Release catalog record {record['key']} is not verified")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("catalog", type=Path)
    parser.add_argument("game_config", type=Path)
    parser.add_argument("source_manifest", type=Path)
    parser.add_argument("source_root", type=Path)
    args = parser.parse_args()
    validate(args.catalog, args.game_config, args.source_manifest, args.source_root)


if __name__ == "__main__":
    main()
