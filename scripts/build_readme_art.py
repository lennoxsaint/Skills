#!/usr/bin/env python3
"""Build the README diagrams in docs/assets/ from catalog.json.

Each diagram is written twice, once for GitHub's light theme and once for its dark theme.
The proof chart reads every number from catalog.json, so the picture cannot drift from the data.

    python3 scripts/build_readme_art.py          # write the SVG files
    python3 scripts/build_readme_art.py --check  # exit 1 if a file is missing or out of date
"""

from __future__ import annotations

import argparse
import json
import sys
from html import escape
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ASSETS = REPO_ROOT / "docs" / "assets"

SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"

THEMES = {
    "light": {
        "bg": "#ffffff", "card": "#f6f8fa", "edge": "#d1d9e0", "ink": "#1f2328", "muted": "#59636e",
        "paper": "#fffdf7", "paper_edge": "#e3dccb", "accent": "#9a6700", "accent_bg": "#fff8c5",
        "levels": {"blind-ab": "#1a7f37", "outside-review": "#0969da", "tested": "#9a6700", "spec": "#818b98"},
        "dot_off": "#d1d9e0",
    },
    "dark": {
        "bg": "#0d1117", "card": "#151b23", "edge": "#3d444d", "ink": "#f0f6fc", "muted": "#9198a1",
        "paper": "#1c1a14", "paper_edge": "#4a4433", "accent": "#e3b341", "accent_bg": "#3b2e0a",
        "levels": {"blind-ab": "#3fb950", "outside-review": "#4493f8", "tested": "#d29922", "spec": "#9198a1"},
        "dot_off": "#3d444d",
    },
}

LEVELS = ["blind-ab", "outside-review", "tested", "spec"]
LEVEL_NAMES = {"blind-ab": "Blind A/B test", "outside-review": "Outside review", "tested": "Tested", "spec": "Spec only"}
LEVEL_DOTS = {"blind-ab": 4, "outside-review": 3, "tested": 2, "spec": 1}

STEPS = [
    ("Do the work", "on your real files, data and pages", "every skill"),
    ("Check it for real", "tests, renders, a re-read of what went live", "Finish Work, Ambitious, Hill Climb"),
    ("Get a second opinion", "a different AI model scores the work", "Ambitious, Hill Climb, Adversarial Review"),
    ("Wait for your yes", "before it sends, posts, buys or deploys", "every skill"),
]

RECEIPT = [
    ("Asked", ["update the prices and", "publish them"]),
    ("True now", ["prices saved locally.", "not published: the", "publish token is missing."]),
    ("Checked", ["./publish.sh: exit 1,", "token not set"]),
    ("Next", ["get the token, then", "run ./publish.sh"]),
]


def text(x, y, body, size, fill, weight=400, anchor="start", family=SANS, spacing=None):
    extra = f' letter-spacing="{spacing}"' if spacing else ""
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}"{extra}>{escape(body)}</text>')


def how_it_works(t: dict) -> str:
    w, h = 800, 600
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d">',
           '<title id="t">What a skill changes</title>',
           '<desc id="d">Four steps a skill adds to how your agent works: do the work, check it for real, get a second '
           'opinion from a different AI model, and wait for your yes before anything goes out. It ends with a receipt. '
           'The sample receipt says the status is blocked: prices saved locally, not published because the publish token is missing.</desc>',
           f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="20" fill="{t["bg"]}" stroke="{t["edge"]}" stroke-width="2"/>',
           text(40, 62, "WHAT A SKILL CHANGES", 15, t["muted"], 600, spacing="1.5"),
           text(40, 104, "From “done!” to a receipt you can check", 30, t["ink"], 700)]
    rail_x, top, gap = 64, 156, 104
    out.append(f'<line x1="{rail_x}" y1="{top}" x2="{rail_x}" y2="{top + gap * 3}" stroke="{t["edge"]}" stroke-width="3"/>')
    for i, (title, line, used_in) in enumerate(STEPS):
        y = top + gap * i
        gate = i == len(STEPS) - 1
        out.append(f'<circle cx="{rail_x}" cy="{y}" r="20" fill="{t["accent_bg"] if gate else t["bg"]}" '
                   f'stroke="{t["accent"] if gate else t["ink"]}" stroke-width="2.5"/>')
        out.append(text(rail_x, y + 7, str(i + 1), 19, t["accent"] if gate else t["ink"], 700, "middle"))
        out.append(text(rail_x + 40, y + 2, title, 25, t["ink"], 700))
        out.append(text(rail_x + 40, y + 30, line, 18, t["muted"]))
        out.append(text(rail_x + 40, y + 54, f"in: {used_in}", 14, t["muted"], 400))
    # arrow from the last step to the receipt
    ay = top + gap * 3
    out.append(f'<path d="M {rail_x} {ay + 20} L {rail_x} {ay + 62} L 470 {ay + 62}" fill="none" stroke="{t["edge"]}" stroke-width="3"/>')
    out.append(f'<path d="M 470 {ay + 54} L 484 {ay + 62} L 470 {ay + 70} Z" fill="{t["edge"]}"/>')
    out.append(text(rail_x + 40, ay + 88, "then it writes down what is proven and what is not", 16, t["muted"]))
    # receipt card with a torn bottom edge
    rx, ry, rw, rh = 492, 140, 272, 420
    zig = " ".join(f"L {rx + rw - k * 17} {ry + rh + (8 if k % 2 else 0)}" for k in range(1, 17))
    out.append(f'<path d="M {rx} {ry} L {rx + rw} {ry} L {rx + rw} {ry + rh} {zig} L {rx} {ry + rh} Z" '
               f'fill="{t["paper"]}" stroke="{t["paper_edge"]}" stroke-width="2" stroke-linejoin="round"/>')
    out.append(text(rx + 22, ry + 38, "RECEIPT", 15, t["muted"], 700, family=MONO, spacing="2"))
    out.append(f'<rect x="{rx + 132}" y="{ry + 18}" width="118" height="30" rx="15" fill="{t["accent_bg"]}"/>')
    out.append(text(rx + 191, ry + 39, "blocked", 16, t["accent"], 700, "middle", MONO))
    y = ry + 82
    for label, lines in RECEIPT:
        out.append(text(rx + 22, y, label, 13, t["muted"], 700, family=MONO, spacing="1"))
        y += 22
        for line in lines:
            out.append(text(rx + 22, y, line, 15, t["ink"], 400, family=MONO))
            y += 21
        y += 12
    out.append(text(rx + 22, ry + rh - 14, "sample from the Finish Work guide", 12, t["muted"], 400, family=MONO))
    out.append("</svg>")
    return "\n".join(out) + "\n"


def proof_chart(t: dict, catalog: dict) -> str:
    skills = sorted(catalog["skills"], key=lambda e: LEVELS.index(e["proof"]["level"]))
    w, row, top = 800, 62, 196
    h = top + row * len(skills) + 52
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d">',
           '<title id="t">Proof so far, by skill</title>',
           '<desc id="d">' + escape(" ".join(
               f'{e["display_name"]}: {LEVEL_NAMES[e["proof"]["level"]]}, {e["proof"]["headline"]} ({e["proof"]["caption"]}).'
               for e in skills)) + '</desc>',
           f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="20" fill="{t["bg"]}" stroke="{t["edge"]}" stroke-width="2"/>',
           text(40, 62, "PROOF SO FAR", 15, t["muted"], 600, spacing="1.5"),
           text(40, 104, "Every skill shows its test results, even the weak ones", 28, t["ink"], 700)]
    lx = 40
    for level in LEVELS:
        color = t["levels"][level]
        for k in range(4):
            out.append(f'<circle cx="{lx + 6 + k * 13}" cy="{143}" r="5" fill="{color if k < LEVEL_DOTS[level] else t["dot_off"]}"/>')
        out.append(text(lx + 58, 148, LEVEL_NAMES[level], 15, t["ink"], 600))
        lx += 58 + round(len(LEVEL_NAMES[level]) * 8.4) + 30
    out.append(f'<line x1="40" y1="{top - 26}" x2="{w - 40}" y2="{top - 26}" stroke="{t["edge"]}" stroke-width="1.5"/>')
    for i, e in enumerate(skills):
        y = top + row * i
        level = e["proof"]["level"]
        color = t["levels"][level]
        if i % 2 == 0:
            out.append(f'<rect x="24" y="{y - 22}" width="{w - 48}" height="{row - 6}" rx="10" fill="{t["card"]}"/>')
        out.append(text(40, y + 14, e["display_name"], 22, t["ink"], 700))
        for k in range(4):
            out.append(f'<circle cx="{348 + k * 17}" cy="{y + 6}" r="6.5" fill="{color if k < LEVEL_DOTS[level] else t["dot_off"]}"/>')
        out.append(text(760, y + 8, e["proof"]["headline"], 24, color, 700, "end"))
        out.append(text(760, y + 28, e["proof"]["caption"], 14, t["muted"], 400, "end"))
    out.append(text(40, h - 24, "Numbers come from catalog.json and the evaluations/ folder.", 14, t["muted"]))
    out.append("</svg>")
    return "\n".join(out) + "\n"


def build() -> dict[Path, str]:
    catalog = json.loads((REPO_ROOT / "catalog.json").read_text(encoding="utf-8"))
    files = {}
    for name, theme in THEMES.items():
        files[ASSETS / f"how-it-works-{name}.svg"] = how_it_works(theme)
        files[ASSETS / f"proof-{name}.svg"] = proof_chart(theme, catalog)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail if a diagram is missing or out of date")
    args = parser.parse_args()
    stale = []
    for path, body in build().items():
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != body:
                stale.append(path.relative_to(REPO_ROOT).as_posix())
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
    if stale:
        print("Out of date, run python3 scripts/build_readme_art.py: " + ", ".join(stale))
        return 1
    print("PASS: README diagrams match catalog.json" if args.check else "Wrote README diagrams to docs/assets/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
