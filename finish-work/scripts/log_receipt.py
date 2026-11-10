#!/usr/bin/env python3
"""Append one work receipt to a dated Markdown log and print the result as JSON.

The log folder is --log-dir, else $FINISH_WORK_LOG_DIR, else ~/.finish-work/log.
One file per local day: YYYY-MM-DD.md. Entries are only ever appended.

Exit code 0 for `written` and `skipped`, 1 for `failed`. Standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

STATUSES = ("completed", "in_progress", "waiting", "blocked", "cancelled", "unknown")
DEFAULT_LOG_DIR = "~/.finish-work/log"


def resolve_log_dir(explicit: str | None) -> Path:
    chosen = explicit if explicit is not None else os.environ.get("FINISH_WORK_LOG_DIR")
    if chosen is None:
        chosen = DEFAULT_LOG_DIR
    if not chosen.strip():
        raise ValueError("the log folder is empty. Set --log-dir or FINISH_WORK_LOG_DIR to a folder, or unset it.")
    return Path(chosen).expanduser()


def one_line(text: str) -> str:
    return " ".join(text.split())


def entry_id(args: argparse.Namespace) -> str:
    identity = [
        args.task_id or "",
        args.status,
        one_line(args.objective),
        one_line(args.outcome),
        one_line(args.scope or ""),
        *[one_line(item) for group in (args.file, args.check, args.decision, args.error, args.next) for item in group],
    ]
    return hashlib.sha256("\x1f".join(identity).encode("utf-8")).hexdigest()[:12]


def bullet_block(title: str, items: list[str]) -> list[str]:
    if not items:
        return [f"- {title}: none recorded"]
    return [f"- {title}:"] + [f"  - {one_line(item)}" for item in items]


def render(args: argparse.Namespace, identifier: str, now: datetime) -> str:
    lines = [
        f"## {now.strftime('%H:%M:%S %z').strip()} - {args.status} - {one_line(args.objective)}",
        "",
        f"- Entry: `{identifier}`",
        f"- Task: {one_line(args.task_id) if args.task_id else 'UNKNOWN'}",
        f"- Status: {args.status}",
        f"- Objective: {one_line(args.objective)}",
        f"- Outcome: {one_line(args.outcome)}",
        f"- Scope: {one_line(args.scope) if args.scope else 'UNKNOWN'}",
        f"- Workspace: {one_line(args.workspace) if args.workspace else os.getcwd()}",
        *bullet_block("Files changed", args.file),
        *bullet_block("Checks and outcomes", args.check),
        *bullet_block("Decisions", args.decision),
        *bullet_block("Errors and fixes", args.error),
        *bullet_block("Next steps", args.next),
        "",
    ]
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Append one work receipt to a dated Markdown log.")
    parser.add_argument("--status", required=True, choices=STATUSES, help="the actual state of the work")
    parser.add_argument("--objective", required=True, help="what was asked")
    parser.add_argument("--outcome", required=True, help="what is true now, in plain words")
    parser.add_argument("--task-id", default=None, help="a stable id for this task, reused across checkpoints")
    parser.add_argument("--scope", default=None, help="what was in and out of scope")
    parser.add_argument("--workspace", default=None, help="the project folder (default: the current folder)")
    parser.add_argument("--file", action="append", default=[], help="a changed file; repeat for more")
    parser.add_argument("--check", action="append", default=[], help="'<command or inspection>: <result>'; repeat for more")
    parser.add_argument("--decision", action="append", default=[], help="a choice made and why; repeat for more")
    parser.add_argument("--error", action="append", default=[], help="a failure and its fix; repeat for more")
    parser.add_argument("--next", action="append", default=[], help="a remaining step; repeat for more")
    parser.add_argument("--log-dir", default=None, help=f"log folder (default: $FINISH_WORK_LOG_DIR, else {DEFAULT_LOG_DIR})")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    for name in ("objective", "outcome"):
        if not getattr(args, name).strip():
            print(json.dumps({"status": "failed", "error": f"--{name} is empty"}))
            return 1
    identifier = entry_id(args)
    now = datetime.now().astimezone()
    try:
        log_dir = resolve_log_dir(args.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        path = log_dir / f"{now.strftime('%Y-%m-%d')}.md"
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
        if f"- Entry: `{identifier}`" in existing:
            print(json.dumps({"status": "skipped", "reason": "this entry is already in the log", "path": str(path), "entry_id": identifier}))
            return 0
        header = "" if existing else f"# Work receipts {now.strftime('%Y-%m-%d')}\n\n"
        separator = "" if not existing or existing.endswith("\n\n") else ("\n" if existing.endswith("\n") else "\n\n")
        with path.open("a", encoding="utf-8") as handle:
            handle.write(header + separator + render(args, identifier, now))
        written = path.read_text(encoding="utf-8")
        if f"- Entry: `{identifier}`" not in written:
            raise OSError("the entry was not found in the log after writing")
    except (OSError, ValueError) as error:
        print(json.dumps({"status": "failed", "error": str(error), "entry_id": identifier}))
        return 1
    print(json.dumps({"status": "written", "path": str(path), "entry_id": identifier}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
