#!/usr/bin/env python3
"""Validate the durable goal-packet contract."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from goal_slug import choose_packet_dir, slugify


SKILL_ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = SKILL_ROOT / "SKILL.md"
GOAL_TEMPLATE_PATH = SKILL_ROOT / "assets" / "goal.md.template"
PROGRESS_TEMPLATE_PATH = SKILL_ROOT / "assets" / "progress.md.template"

REQUIRED_SKILL_TERMS = (
    ".codex/goals/<goal-slug>/",
    "goal.md` is owner-editable",
    "progress.md` is Codex-owned",
    "latest explicit instruction in the active thread",
    "Re-read `goal.md` before each checkpoint",
    "SHA-256",
    "Compute the SHA-256 of that saved file",
    "goal_slug.py",
    "without overwriting an existing packet",
    "Do not edit `.gitignore`, stage, or commit",
    "Do not start the goal unless",
    "Claude",
    "4,000 characters",
    "three times",
)

REQUIRED_GOAL_HEADINGS = (
    "## Outcome",
    "## Workspace and source truth",
    "## Success and loop criteria",
    "## Autonomy",
    "## Hard stop rules",
    "## Required work",
    "## Verification",
    "## Steering notes",
    "## Final report",
)

REQUIRED_PROGRESS_HEADINGS = (
    "## Current checkpoint",
    "## Verified evidence",
    "## Remaining work",
    "## Blockers",
    "## Accepted steering",
    "## Decisions and strategy changes",
    "## Next action",
)


def errors() -> list[str]:
    failures: list[str] = []

    for path in (SKILL_PATH, GOAL_TEMPLATE_PATH, PROGRESS_TEMPLATE_PATH):
        if not path.is_file():
            failures.append(f"missing file: {path}")

    if failures:
        return failures

    skill = SKILL_PATH.read_text(encoding="utf-8")
    goal_template = GOAL_TEMPLATE_PATH.read_text(encoding="utf-8")
    progress_template = PROGRESS_TEMPLATE_PATH.read_text(encoding="utf-8")

    for term in REQUIRED_SKILL_TERMS:
        if term not in skill:
            failures.append(f"SKILL.md missing required contract term: {term}")

    for heading in REQUIRED_GOAL_HEADINGS:
        if heading not in goal_template:
            failures.append(f"goal template missing heading: {heading}")

    for heading in REQUIRED_PROGRESS_HEADINGS:
        if heading not in progress_template:
            failures.append(f"progress template missing heading: {heading}")

    if "/goal Execute the goal contract at" not in skill:
        failures.append("SKILL.md missing the native Goal Mode launcher")

    if "native /goal as the lifecycle authority" not in skill:
        failures.append("SKILL.md must keep native /goal authoritative")

    if "send, publish, delete, charge" not in skill:
        failures.append("SKILL.md missing explicit live-action denials")

    slug_cases = {
        "Migrate Duo Search to the New Index": "migrate-duo-search-to-the-new-index",
        "  Ship: Mobile / Desktop parity!  ": "ship-mobile-desktop-parity",
        "A" * 80: "a" * 64,
        "": "goal",
    }
    for title, expected in slug_cases.items():
        actual = slugify(title)
        if actual != expected:
            failures.append(
                f"slug mismatch for {title!r}: expected {expected!r}, got {actual!r}"
            )

    with tempfile.TemporaryDirectory(prefix="goal-skill-test-") as temp_dir:
        workspace = Path(temp_dir) / "Workspace With Spaces"
        first = choose_packet_dir(workspace, "Migrate Duo Search", reserve=True)
        second = choose_packet_dir(workspace, "Migrate Duo Search", reserve=True)
        if first.name != "migrate-duo-search":
            failures.append(f"unexpected first packet slug: {first.name}")
        if second.name != "migrate-duo-search-2":
            failures.append(f"collision suffix was not reserved: {second.name}")
        if first.parent != second.parent or "Workspace With Spaces" not in str(first):
            failures.append("packet helper mishandled the spaced workspace path")
        long_first = choose_packet_dir(workspace, "A" * 80, reserve=True)
        long_second = choose_packet_dir(workspace, "A" * 80, reserve=True)
        if len(long_first.name) > 64 or len(long_second.name) > 64:
            failures.append("packet helper exceeded the 64-character slug cap")

    return failures


def main() -> int:
    failures = errors()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("PASS: goal skill durable packet contract is valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
