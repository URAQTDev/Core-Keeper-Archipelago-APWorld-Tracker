"""Query the pinned Core Keeper runtime database by exact or partial name."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    parser.add_argument("names", nargs="+")
    parser.add_argument("--partial", action="store_true")
    args = parser.parse_args()

    payload = json.loads(args.database.read_text(encoding="utf-8"))
    objects = payload["records"]
    queries = [name.casefold() for name in args.names]
    for query, original in zip(queries, args.names):
        matches = []
        for record in objects:
            names = (record.get("internal_name", ""), record.get("display_name", ""))
            folded = tuple(name.casefold() for name in names)
            matched = any(query in name for name in folded) if args.partial else query in folded
            if matched:
                matches.append(record)
        print(f"[{original}]")
        for record in matches:
            print(
                f"{record['object_id']}\t{record['internal_name']}\t"
                f"{record['display_name']}\tvariation={record.get('variation', 0)}"
            )


if __name__ == "__main__":
    main()
