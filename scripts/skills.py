#!/usr/bin/env python3
"""List, validate, inspect, and safely install skills from this repository."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = REPO_ROOT / "catalog.json"
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class CatalogError(ValueError):
    pass


def load_catalog() -> dict:
    try:
        payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CatalogError(f"Cannot read {CATALOG_PATH}: {error}") from error
    if payload.get("schema_version") != "1.0" or not isinstance(payload.get("skills"), list):
        raise CatalogError("catalog.json must use schema_version 1.0 and contain a skills list")
    return payload


def skill_by_name(name: str) -> dict:
    matches = [entry for entry in load_catalog()["skills"] if entry.get("name") == name]
    if len(matches) != 1:
        available = ", ".join(sorted(entry.get("name", "?") for entry in load_catalog()["skills"]))
        raise CatalogError(f"Unknown skill {name!r}. Available: {available or 'none'}")
    return matches[0]


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise CatalogError(f"{path}: missing YAML frontmatter")
    try:
        frontmatter, _body = text[4:].split("\n---\n", 1)
    except ValueError as error:
        raise CatalogError(f"{path}: frontmatter is not closed") from error
    fields: dict[str, str] = {}
    for line in frontmatter.splitlines():
        if not line or line.startswith((" ", "\t")) or ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip()
    if list(fields) != ["name", "description"]:
        raise CatalogError(f"{path}: frontmatter keys must be exactly name, description")
    return fields


def validate_repository() -> list[str]:
    catalog = load_catalog()
    errors: list[str] = []
    names: set[str] = set()
    paths: set[str] = set()
    required_catalog_fields = {
        "name", "display_name", "path", "status", "version", "summary",
        "requires", "docs", "evaluation", "examples", "trigger_cases",
    }

    for entry in catalog["skills"]:
        missing = sorted(required_catalog_fields - set(entry))
        if missing:
            errors.append(f"catalog entry missing fields: {', '.join(missing)}")
            continue
        name = entry["name"]
        relative_path = entry["path"]
        if name in names:
            errors.append(f"duplicate skill name: {name}")
        if relative_path in paths:
            errors.append(f"duplicate skill path: {relative_path}")
        names.add(name)
        paths.add(relative_path)
        if not NAME_PATTERN.fullmatch(name):
            errors.append(f"invalid skill name: {name}")
        if relative_path != name:
            errors.append(f"{name}: catalog path must match the skill name")

        skill_dir = REPO_ROOT / relative_path
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            errors.append(f"{name}: missing {skill_md.relative_to(REPO_ROOT)}")
            continue
        try:
            frontmatter = parse_frontmatter(skill_md)
        except (CatalogError, OSError) as error:
            errors.append(str(error))
            continue
        if frontmatter["name"] != name:
            errors.append(f"{name}: SKILL.md name is {frontmatter['name']!r}")
        skill_text = skill_md.read_text(encoding="utf-8")
        if "TODO" in skill_text:
            errors.append(f"{name}: SKILL.md contains TODO")
        if (skill_dir / "README.md").exists():
            errors.append(f"{name}: README.md belongs at repository level, not inside a skill folder")
        if not (skill_dir / "agents" / "openai.yaml").is_file():
            errors.append(f"{name}: missing agents/openai.yaml")
        for reference in re.findall(r"\]\((references/[^)]+)\)", skill_text):
            if not (skill_dir / reference).is_file():
                errors.append(f"{name}: missing linked reference {reference}")
        for script in (skill_dir / "scripts").glob("*.py"):
            try:
                compile(script.read_text(encoding="utf-8"), str(script), "exec")
            except SyntaxError as error:
                errors.append(f"{name}: Python syntax error in {script.name}: {error}")

        for key in ("docs", "evaluation", "examples", "trigger_cases"):
            if not (REPO_ROOT / entry[key]).exists():
                errors.append(f"{name}: missing catalog {key} path {entry[key]}")
        trigger_path = REPO_ROOT / entry["trigger_cases"]
        if trigger_path.is_file():
            try:
                cases = json.loads(trigger_path.read_text(encoding="utf-8"))
                prompts = [case["prompt"] for case in cases]
                if len(prompts) != len(set(prompts)):
                    errors.append(f"{name}: trigger prompts must be unique")
                if sum(case.get("should_trigger") is True for case in cases) < 20:
                    errors.append(f"{name}: needs at least 20 positive trigger cases")
                if sum(case.get("should_trigger") is False for case in cases) < 20:
                    errors.append(f"{name}: needs at least 20 negative trigger cases")
            except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
                errors.append(f"{name}: invalid trigger case bank: {error}")

    actual_skill_dirs = {
        path.parent.name
        for path in REPO_ROOT.glob("*/SKILL.md")
        if ".git" not in path.parts
    }
    uncatalogued = sorted(actual_skill_dirs - names)
    if uncatalogued:
        errors.append(f"uncatalogued skill folders: {', '.join(uncatalogued)}")

    readme_path = REPO_ROOT / "README.md"
    if not readme_path.is_file():
        errors.append("missing repository README.md")
    else:
        readme = readme_path.read_text(encoding="utf-8")
        for entry in catalog["skills"]:
            expected_link = f"[{entry['display_name']}]({entry['path']}/SKILL.md)"
            if expected_link not in readme:
                errors.append(f"{entry['name']}: missing from the README skill table")
            if f"| {entry['version']} |" not in readme:
                errors.append(f"{entry['name']}: README version does not match catalog")

    for markdown_path in REPO_ROOT.rglob("*.md"):
        if ".git" in markdown_path.parts:
            continue
        markdown = markdown_path.read_text(encoding="utf-8")
        for target in re.findall(r"\]\(([^)]+)\)", markdown):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            relative = target.split("#", 1)[0]
            if relative and not (markdown_path.parent / relative).resolve().exists():
                errors.append(
                    f"{markdown_path.relative_to(REPO_ROOT)}: broken local link {target}"
                )
    return errors


def command_list(_args: argparse.Namespace) -> int:
    print("NAME                 STATUS   VERSION  DESCRIPTION")
    for entry in load_catalog()["skills"]:
        print(f"{entry['name']:<20} {entry['status']:<8} {entry['version']:<8} {entry['summary']}")
    return 0


def command_show(args: argparse.Namespace) -> int:
    print(json.dumps(skill_by_name(args.name), indent=2, sort_keys=True))
    return 0


def command_validate(_args: argparse.Namespace) -> int:
    errors = validate_repository()
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"PASS: {len(load_catalog()['skills'])} catalogued skill(s) validated")
    return 0


def command_install(args: argparse.Namespace) -> int:
    errors = validate_repository()
    if errors:
        raise CatalogError("Repository validation failed; run `python3 scripts/skills.py validate`")
    entry = skill_by_name(args.name)
    source = REPO_ROOT / entry["path"]
    target_root = Path(args.target_root).expanduser().resolve()
    destination = target_root / entry["name"]
    if destination.exists():
        raise CatalogError(
            f"Refusing to overwrite {destination}. Rename or remove it after reviewing your local copy, then rerun."
        )
    target_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{entry['name']}-", dir=target_root) as staging_root:
        staged = Path(staging_root) / entry["name"]
        shutil.copytree(
            source,
            staged,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", "test_*.py"),
        )
        os.replace(staged, destination)
    print(f"Installed {entry['display_name']} to {destination}")
    print(f"Try: Use ${entry['name']} to help me with this task.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Browse and install skills from lennoxsaint/Skills")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("list", help="List all public skills").set_defaults(handler=command_list)
    show = subparsers.add_parser("show", help="Show machine-readable metadata for one skill")
    show.add_argument("name")
    show.set_defaults(handler=command_show)
    subparsers.add_parser("validate", help="Validate the catalog and every skill").set_defaults(handler=command_validate)
    install = subparsers.add_parser("install", help="Install one skill without overwriting an existing copy")
    install.add_argument("name")
    install.add_argument(
        "--target-root",
        default=str(Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "skills"),
        help="Skills directory; defaults to $CODEX_HOME/skills or ~/.codex/skills",
    )
    install.set_defaults(handler=command_install)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.handler(args)
    except CatalogError as error:
        parser.error(str(error))


if __name__ == "__main__":
    raise SystemExit(main())
