#!/usr/bin/env python3
"""Append one work receipt to a dated Markdown log and print the result as JSON.

The log folder is --log-dir, else $FINISH_WORK_LOG_DIR, else ~/.finish-work/log.
One file per local day: YYYY-MM-DD.md. Entries are only ever appended.

Every entry ends with a marker line. A receipt counts as already written only
when its whole entry, from the id line to the marker, is in today's or
yesterday's file exactly as this helper would write it.

Exit code 0 for `written` and `skipped`, 1 for `failed`, 2 for a usage error.
Standard library only.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    import fcntl
except ImportError:  # no fcntl on Windows: the helper runs without the lock there
    fcntl = None

STATUSES = ("completed", "in_progress", "waiting", "blocked", "cancelled", "unknown")
DEFAULT_LOG_DIR = "~/.finish-work/log"
LOCK_NAME = ".receipts.lock"
LISTS = ("file", "check", "decision", "error", "next")


def resolve_log_dir(explicit: str | None) -> Path:
    chosen = explicit if explicit is not None else os.environ.get("FINISH_WORK_LOG_DIR")
    if chosen is None:
        chosen = DEFAULT_LOG_DIR
    if not chosen.strip():
        raise ValueError("the log folder is empty. Set --log-dir or FINISH_WORK_LOG_DIR to a folder, or unset it.")
    return Path(chosen).expanduser()


def one_line(text: str) -> str:
    """Collapse all whitespace to single spaces and drop characters UTF-8 cannot store."""
    return " ".join(text.encode("utf-8", "replace").decode("utf-8").split())


def clean_fields(args: argparse.Namespace) -> dict:
    """Every recorded value, cleaned once. The entry id and the entry text both come from this."""
    fields = {
        "task_id": one_line(args.task_id or ""),
        "status": args.status,
        "objective": one_line(args.objective),
        "outcome": one_line(args.outcome),
        "scope": one_line(args.scope or ""),
        "workspace": one_line(args.workspace or os.getcwd()),
    }
    for name in LISTS:
        fields[name] = [one_line(item) for item in getattr(args, name)]
    return fields


def entry_id(fields: dict) -> str:
    canonical = json.dumps(fields, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("ascii")).hexdigest()[:12]


def end_marker(identifier: str) -> str:
    return f"<!-- receipt-end {identifier} -->"


def current_time() -> datetime:
    return datetime.now().astimezone()


def has_complete_entry(text: str, body: str) -> bool:
    """True only when every line of the entry, id line to closing marker, is in the file in order.

    A lone id line or a lone marker is a fragment, not a receipt. Values passed on the
    command line are each written on one line, so no argument can contain this block.
    """
    return "\n" + body in "\n" + text


def bullet_block(title: str, items: list[str]) -> list[str]:
    if not items:
        return [f"- {title}: none recorded"]
    return [f"- {title}:"] + [f"  - {item}" for item in items]


def render_body(fields: dict, identifier: str) -> str:
    """The part of an entry that depends only on what was recorded, not on when."""
    lines = [
        f"- Entry: `{identifier}`",
        f"- Task: {fields['task_id'] or 'UNKNOWN'}",
        f"- Status: {fields['status']}",
        f"- Objective: {fields['objective']}",
        f"- Outcome: {fields['outcome']}",
        f"- Scope: {fields['scope'] or 'UNKNOWN'}",
        f"- Workspace: {fields['workspace']}",
        *bullet_block("Files changed", fields["file"]),
        *bullet_block("Checks and outcomes", fields["check"]),
        *bullet_block("Decisions", fields["decision"]),
        *bullet_block("Errors and fixes", fields["error"]),
        *bullet_block("Next steps", fields["next"]),
        "",
        end_marker(identifier),
    ]
    return "\n".join(lines) + "\n"


def render(fields: dict, identifier: str, now: datetime) -> str:
    heading = f"## {now.strftime('%H:%M:%S %z').strip()} - {fields['status']} - {fields['objective']}"
    return heading + "\n\n" + render_body(fields, identifier) + "\n"


@contextlib.contextmanager
def log_lock(log_dir: Path):
    """Let one helper at a time check and append. Without fcntl the block runs unlocked."""
    if fcntl is None:
        yield
        return
    with (log_dir / LOCK_NAME).open("a", encoding="utf-8") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


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
    result: dict = {"status": "failed"}
    try:
        fields = clean_fields(args)
        for name in ("objective", "outcome"):
            if not fields[name]:
                raise ValueError(f"--{name} is empty")
        identifier = entry_id(fields)
        result["entry_id"] = identifier
        body = render_body(fields, identifier)
        log_dir = resolve_log_dir(args.log_dir)
        result["path"] = str(log_dir / f"{current_time().strftime('%Y-%m-%d')}.md")
        log_dir.mkdir(parents=True, exist_ok=True)
        with log_lock(log_dir):
            # Read the clock only once the lock is held: a run that waited past midnight
            # must look in the new day's file, where the run it waited for has written.
            now = current_time()
            path = log_dir / f"{now.strftime('%Y-%m-%d')}.md"
            result["path"] = str(path)
            yesterday = log_dir / f"{(now - timedelta(days=1)).strftime('%Y-%m-%d')}.md"
            for candidate in (path, yesterday):
                if has_complete_entry(read_text(candidate), body):
                    result.update(status="skipped", reason="this receipt is already in the log", path=str(candidate))
                    print(json.dumps(result))
                    return 0
            existing = read_text(path)
            header = "" if existing else f"# Work receipts {now.strftime('%Y-%m-%d')}\n\n"
            separator = "" if not existing or existing.endswith("\n\n") else ("\n" if existing.endswith("\n") else "\n\n")
            with path.open("a", encoding="utf-8") as handle:
                handle.write(header + separator + render(fields, identifier, now))
                handle.flush()
                os.fsync(handle.fileno())
            if not has_complete_entry(read_text(path), body):
                raise OSError("the complete entry was not found in the log after writing")
    except (OSError, ValueError, RuntimeError) as error:  # RuntimeError: "~name" with no such user
        result.update(status="failed", error=str(error))
        print(json.dumps(result))
        return 1
    result["status"] = "written"
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
