"""Create a deterministic PopTracker pack archive."""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path


EXCLUDED_SUFFIXES = {".pyc"}


def build(source: Path, output: Path) -> None:
    files = sorted(
        path for path in source.rglob("*")
        if path.is_file()
        and path.suffix not in EXCLUDED_SUFFIXES
        and "__pycache__" not in path.parts
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            relative = path.relative_to(source).as_posix()
            info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes(), compresslevel=9)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    build(args.source, args.output)


if __name__ == "__main__":
    main()
