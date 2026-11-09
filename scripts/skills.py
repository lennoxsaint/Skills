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
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = REPO_ROOT / "catalog.json"
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CODE_SPAN_PATTERN = re.compile(r"```.*?```|`[^`\n]*`", re.DOTALL)
HOSTS = ("claude", "codex")


def host_skill_root(host: str) -> Path:
    """Return the personal skills folder for one host, honouring its config-home variable."""
    if host == "claude":
        return Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude") / "skills"
    if host == "codex":
        return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex") / "skills"
    raise CatalogError(f"Unknown host {host!r}. Use one of: {', '.join(HOSTS)}, both")


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
        "use_when", "try", "hosts",
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
        # A skill may name the literal word in code formatting (for example a "no `TODO` remains" check).
        if "TODO" in CODE_SPAN_PATTERN.sub("", skill_text):
            errors.append(f"{name}: SKILL.md contains TODO")
        for key in ("use_when", "try"):
            if not isinstance(entry[key], str) or not entry[key].strip():
                errors.append(f"{name}: catalog {key} must be a non-empty string")
        if not isinstance(entry["hosts"], list) or not entry["hosts"] or set(entry["hosts"]) - set(HOSTS):
            errors.append(f"{name}: catalog hosts must list one or more of {', '.join(HOSTS)}")
        if (skill_dir / "README.md").exists():
            errors.append(f"{name}: README.md belongs at repository level, not inside a skill folder")
        if not (skill_dir / "agents" / "openai.yaml").is_file():
            errors.append(f"{name}: missing agents/openai.yaml")
        for reference in re.findall(r"\]\((references/[^)]+)\)", skill_text):
            if not (skill_dir / reference.split("#", 1)[0]).is_file():
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
    print("NAME                 STATUS   VERSION  USE WHEN")
    for entry in load_catalog()["skills"]:
        print(f"{entry['name']:<20} {entry['status']:<8} {entry['version']:<8} {entry['use_when']}")
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


def install_one(entry: dict, target_root: Path, update: bool) -> Path:
    source = REPO_ROOT / entry["path"]
    destination = target_root / entry["name"]
    backup = None
    if destination.exists():
        if not update:
            raise CatalogError(
                f"Refusing to overwrite {destination}. Rerun with --update to replace it "
                "(the old copy is moved to a backup folder first), or remove it yourself."
            )
        # The backup lives beside the skills folder, never inside it, so a host cannot load it as a second skill.
        backup = target_root.parent / "skills-backup" / f"{entry['name']}-{time.strftime('%Y%m%d-%H%M%S')}"
        if backup.exists():
            raise CatalogError(f"Backup path already exists: {backup}. Wait a second and rerun.")
    target_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{entry['name']}-", dir=target_root) as staging_root:
        staged = Path(staging_root) / entry["name"]
        shutil.copytree(
            source,
            staged,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", "test_*.py"),
        )
        if backup is not None:
            backup.parent.mkdir(parents=True, exist_ok=True)
            os.replace(destination, backup)
        os.replace(staged, destination)
    if backup is not None:
        print(f"Moved the previous copy to {backup}")
    return destination


def command_install(args: argparse.Namespace) -> int:
    errors = validate_repository()
    if errors:
        raise CatalogError("Repository validation failed; run `python3 scripts/skills.py validate`")
    entries = [skill_by_name(name) for name in dict.fromkeys(args.names)]
    if args.target_root is not None:
        if not args.target_root.strip():
            raise CatalogError("--target-root is empty. Name the skills folder to install into, or use --host.")
        roots = [("custom", Path(args.target_root).expanduser().resolve())]
    else:
        hosts = HOSTS if args.host == "both" else (args.host,)
        # Two hosts can share one folder (same config home, or a symlink). Install there once.
        by_root: dict[Path, list[str]] = {}
        for host in hosts:
            by_root.setdefault(host_skill_root(host).expanduser().resolve(), []).append(host)
        roots = [("+".join(names), root) for root, names in by_root.items()]
    # Check every destination before writing anything, so a refusal leaves no half-finished install.
    if not args.update:
        blocked = [str(root / entry["name"]) for _host, root in roots for entry in entries if (root / entry["name"]).exists()]
        if blocked:
            raise CatalogError(
                f"Refusing to overwrite {', '.join(blocked)}. Rerun with --update to replace "
                "(the old copy is moved to a backup folder first), or remove it yourself."
            )
    for entry in entries:
        for host, root in roots:
            destination = install_one(entry, root, args.update)
            print(f"Installed {entry['name']} {entry['version']} to {destination} ({host})")
        print(f"Needs: {entry['requires']}")
        print(f"Try: {entry['try']}")
    print("Start a new session (or restart the app) if the skill does not show up right away.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Browse and install skills from lennoxsaint/Skills")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("list", help="List all public skills").set_defaults(handler=command_list)
    show = subparsers.add_parser("show", help="Show machine-readable metadata for one skill")
    show.add_argument("name")
    show.set_defaults(handler=command_show)
    subparsers.add_parser("validate", help="Validate the catalog and every skill").set_defaults(handler=command_validate)
    install = subparsers.add_parser(
        "install",
        help="Install one or more skills for Claude Code, Codex, or both",
        description=(
            "Copy skills into a host's personal skills folder. "
            "claude: $CLAUDE_CONFIG_DIR/skills or ~/.claude/skills. "
            "codex: $CODEX_HOME/skills or ~/.codex/skills."
        ),
    )
    install.add_argument("names", nargs="+", metavar="name", help="Skill name from `list`; pass several to install several")
    install.add_argument(
        "--host",
        choices=(*HOSTS, "both"),
        default="codex",
        help="Which agent to install for (default: codex)",
    )
    install.add_argument(
        "--target-root",
        help="Install into this skills directory instead of a host default",
    )
    install.add_argument(
        "--update",
        action="store_true",
        help="Replace an installed copy; the old copy is moved to a skills-backup folder first",
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
