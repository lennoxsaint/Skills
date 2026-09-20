#!/usr/bin/env python3
"""Choose or reserve a deterministic, collision-safe goal packet path."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def slugify(title: str) -> str:
    words = re.findall(r"[a-z0-9]+", title.lower())[:8]
    slug = "-".join(words)[:64].rstrip("-")
    return slug or "goal"


def choose_packet_dir(workspace_root: Path, title: str, reserve: bool) -> Path:
    goals_root = workspace_root.resolve() / ".codex" / "goals"
    if reserve:
        goals_root.mkdir(parents=True, exist_ok=True)

    base_slug = slugify(title)
    suffix = 1
    while True:
        if suffix == 1:
            packet_slug = base_slug
        else:
            suffix_text = f"-{suffix}"
            packet_slug = f"{base_slug[: 64 - len(suffix_text)].rstrip('-')}{suffix_text}"
        packet_dir = goals_root / packet_slug
        if reserve:
            try:
                packet_dir.mkdir()
                return packet_dir
            except FileExistsError:
                suffix += 1
                continue
        if not packet_dir.exists():
            return packet_dir
        suffix += 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace-root", required=True, type=Path)
    parser.add_argument("--title", required=True)
    parser.add_argument(
        "--reserve",
        action="store_true",
        help="Create the unique packet directory before returning it.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    packet_dir = choose_packet_dir(args.workspace_root, args.title, args.reserve)
    result = {
        "goal_slug": packet_dir.name,
        "packet_dir": str(packet_dir),
        "goal_path": str(packet_dir / "goal.md"),
        "progress_path": str(packet_dir / "progress.md"),
        "reserved": args.reserve,
    }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
