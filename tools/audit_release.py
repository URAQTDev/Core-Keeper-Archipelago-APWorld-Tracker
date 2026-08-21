"""Reject private runtime state and development files from release artifacts."""

from __future__ import annotations

import argparse
import re
import zipfile
from pathlib import Path


TEXT_SUFFIXES = {
    ".cs", ".json", ".lua", ".md", ".ps1", ".py", ".txt", ".yaml", ".yml"
}
FORBIDDEN_NAMES = (
    ".apsave", "player.log", "player-prev.log", "connection.json",
    "reward-state", "receiveditemcursors", "receiveditemsignatures",
    "pendinglocationchecks", "rewardprovenance", "licenselevels",
    "skillpointlevels", "legendarylevels",
)
FORBIDDEN_TEXT = (
    re.compile(r"C:\\Users\\", re.IGNORECASE),
    re.compile(r"C:\\ProgramData\\", re.IGNORECASE),
    re.compile(r"AppData\\LocalLow", re.IGNORECASE),
    re.compile(r"Steam\\82527651", re.IGNORECASE),
)


def audit_member(name: str, payload: bytes) -> list[str]:
    issues: list[str] = []
    lowered = name.casefold()
    if any(marker in lowered for marker in FORBIDDEN_NAMES):
        issues.append(f"forbidden file name: {name}")
    if Path(name).suffix.casefold() in TEXT_SUFFIXES:
        text = payload.decode("utf-8", errors="ignore")
        for pattern in FORBIDDEN_TEXT:
            if pattern.search(text):
                issues.append(f"private local path in {name}: {pattern.pattern}")
    return issues


def audit_archive(path: Path) -> list[str]:
    issues: list[str] = []
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            issues.extend(audit_member(info.filename, archive.read(info)))
    return issues


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("release", type=Path)
    args = parser.parse_args()
    release = args.release.resolve()
    mod_archives = {
        path.name for path in release.glob("CoreKeeperArchipelago-*.zip")
        if not path.name.startswith("CoreKeeperArchipelago-Tracker-Setup-")
        and not path.name.endswith("-COMPLETE.zip")
        and not path.name.endswith("-MODIO.zip")
    }
    if len(mod_archives) != 1:
        raise SystemExit(
            f"Release audit failed: expected one client mod archive, got {sorted(mod_archives)}"
        )
    mod_archive = next(iter(mod_archives))
    version = mod_archive.removeprefix("CoreKeeperArchipelago-").removesuffix(".zip")
    expected = {
        "core_keeper.apworld",
        f"core_keeper_poptracker_texture_free_{version}.zip",
        f"CoreKeeperArchipelago-Tracker-Setup-{version}.zip",
        *mod_archives,
        f"CoreKeeperArchipelago-{version}-MODIO.zip",
        f"CoreKeeperArchipelago-{version}-COMPLETE.zip",
        "README.md",
        "LICENSE",
        "ASSET_NOTICE.md",
        "THIRD_PARTY_NOTICES.md",
        "SHA256SUMS.txt",
    }
    present = {path.name for path in release.iterdir() if path.is_file()}
    issues = [f"release file mismatch: expected {sorted(expected)}, got {sorted(present)}"] \
        if present != expected else []
    for path in sorted(release.iterdir()):
        if path.is_file() and path.suffix.casefold() in {".zip", ".apworld"}:
            issues.extend(audit_archive(path))
    if issues:
        raise SystemExit("Release audit failed:\n- " + "\n- ".join(issues))
    print(f"Release privacy and contents audit passed for {release}.")


if __name__ == "__main__":
    main()
