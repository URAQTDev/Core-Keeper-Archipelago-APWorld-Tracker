"""Create the deterministic, checksum-locked Core Keeper release set."""

from __future__ import annotations

import hashlib
import shutil
import sys
import zipfile
from pathlib import Path


VERSION = "0.9.0-rc.8"
ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_mod_archive(
    source: Path, output: Path, extras: Path | tuple[Path, ...] = ()
) -> None:
    if isinstance(extras, Path):
        extras = (extras,)
    with zipfile.ZipFile(
        output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for path in sorted(source.rglob("*"), key=lambda item: item.as_posix()):
            if not path.is_file():
                continue
            relative = Path("CoreKeeperArchipelago") / path.relative_to(source)
            info = zipfile.ZipInfo(relative.as_posix(), ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        for extra in extras:
            info = zipfile.ZipInfo(
                f"CoreKeeperArchipelago/{extra.name}", ZIP_TIME
            )
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(
                info,
                extra.read_bytes(),
                compress_type=zipfile.ZIP_DEFLATED,
                compresslevel=9,
            )


def write_modio_archive(
    source: Path, output: Path, extras: Path | tuple[Path, ...] = ()
) -> None:
    """Write the layout Core Keeper's mod.io loader expects.

    Unlike the manual-install archive, ModManifest.json must be at the ZIP root.
    mod.io supplies the enclosing installation directory when it extracts the file.
    """
    if isinstance(extras, Path):
        extras = (extras,)
    with zipfile.ZipFile(
        output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for path in sorted(source.rglob("*"), key=lambda item: item.as_posix()):
            if not path.is_file():
                continue
            info = zipfile.ZipInfo(path.relative_to(source).as_posix(), ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        for extra in extras:
            info = zipfile.ZipInfo(extra.name, ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, extra.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def write_complete_archive(release: Path, output: Path, instructions: Path) -> None:
    entries = {
        "1-core_keeper.apworld": release / "core_keeper.apworld",
        f"2-PopTracker-Pack-TEXTURE-FREE-{VERSION}.zip":
            release / f"core_keeper_poptracker_texture_free_{VERSION}.zip",
        f"3-OPTIONAL-Textured-Tracker-Setup-{VERSION}.zip":
            release / f"CoreKeeperArchipelago-Tracker-Setup-{VERSION}.zip",
    }
    with zipfile.ZipFile(
        output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for name, source in entries.items():
            info = zipfile.ZipInfo(name, ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, source.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        info = zipfile.ZipInfo("START-HERE.txt", ZIP_TIME)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        text = instructions.read_text(encoding="utf-8").replace("{VERSION}", VERSION)
        archive.writestr(info, text.encode("utf-8"), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def package(root: Path) -> Path:
    dist = root / "dist"
    release = dist / f"CoreKeeperArchipelago-{VERSION}"
    release.mkdir(parents=True, exist_ok=True)

    for stale in release.iterdir():
        if stale.is_file():
            stale.unlink()
        elif stale.is_dir():
            shutil.rmtree(stale)

    artifacts = {
        "core_keeper.apworld": dist / "core_keeper.apworld",
        f"core_keeper_poptracker_texture_free_{VERSION}.zip":
            dist / f"core_keeper_poptracker_texture_free_{VERSION}.zip",
        f"CoreKeeperArchipelago-Tracker-Setup-{VERSION}.zip":
            dist / f"CoreKeeperArchipelago-Tracker-Setup-{VERSION}.zip",
    }
    for name, source in artifacts.items():
        if not source.is_file():
            raise FileNotFoundError(source)
        shutil.copyfile(source, release / name)

    mod_source = dist / "CoreKeeperArchipelago"
    if not (mod_source / "ModManifest.json").is_file():
        raise FileNotFoundError(mod_source / "ModManifest.json")
    mod_name = f"CoreKeeperArchipelago-{VERSION}.zip"
    modio_name = f"CoreKeeperArchipelago-{VERSION}-MODIO.zip"
    notice = root / "THIRD_PARTY_NOTICES.md"
    license_path = root / "LICENSE"
    asset_notice = root / "ASSET_NOTICE.md"
    readme = root / "RELEASE_README.md"
    if not all(path.is_file() for path in (notice, license_path, asset_notice, readme)):
        raise FileNotFoundError("Release notices are missing.")
    write_mod_archive(mod_source, release / mod_name, (license_path, notice, asset_notice))
    write_modio_archive(mod_source, release / modio_name, (license_path, notice, asset_notice))
    for extra in (license_path, notice, asset_notice):
        shutil.copyfile(extra, release / extra.name)
    shutil.copyfile(readme, release / "README.md")

    complete_name = f"CoreKeeperArchipelago-{VERSION}-COMPLETE.zip"
    write_complete_archive(release, release / complete_name, root / "PACKAGE_START_HERE.txt")

    names = sorted([*artifacts, mod_name, modio_name, complete_name, license_path.name, notice.name, asset_notice.name, "README.md"])
    checksums = "".join(f"{sha256(release / name)}  {name}\n" for name in names)
    (release / "SHA256SUMS.txt").write_text(checksums, encoding="ascii", newline="\n")
    return release


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: package_release.py <mainline-root>")
    result = package(Path(sys.argv[1]).resolve())
    print(f"Packaged Core Keeper Archipelago {VERSION} release at {result}")
