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
import textwrap
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
    ("Get a second opinion", "a second AI, usually another model, scores it", "Ambitious, Hill Climb, Adversarial Review"),
    ("Wait for your yes", "before it sends, posts, buys or deploys", "every skill"),
]

RECEIPT = [
    ("Asked", "update the prices and publish them"),
    ("True now", "prices saved locally. not published: the publish token is missing."),
    ("Checked", "./publish.sh: exit 1, token not set"),
    ("Next", "get the token, then run ./publish.sh"),
]

# Both diagrams are drawn narrow (440 px) with large text. GitHub shows them about
# 324 px wide on a 390 px phone, so 18 px text here still reads at about 13 px there.
WIDTH = 440


def wrap(body: str, size: float, room: float, mono: bool = False, bold: bool = False) -> list[str]:
    """Split text into lines that fit `room` px, using a cautious average glyph width."""
    per_char = size * (0.61 if mono else 0.53 if bold else 0.47)
    return textwrap.wrap(body, max(8, int(room // per_char))) or [""]


def text(x, y, body, size, fill, weight=400, anchor="start", family=SANS, spacing=None):
    extra = f' letter-spacing="{spacing}"' if spacing else ""
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}"{extra}>{escape(body)}</text>')


def lines(out, x, y, body, size, fill, room, gap, weight=400, family=SANS, mono=False):
    """Write wrapped text and return the y below it."""
    for line in wrap(body, size, room, mono, weight >= 600):
        out.append(text(x, y, line, size, fill, weight, family=family))
        y += gap
    return y


def frame(w, h, t, title, desc):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d">',
            f'<title id="t">{escape(title)}</title>', f'<desc id="d">{escape(desc)}</desc>',
            f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="20" fill="{t["bg"]}" stroke="{t["edge"]}" stroke-width="2"/>']


HOW_DESC = ("The pattern these skills share, step by step. Not every skill does every step. "
            + " ".join(f"Step {i + 1}, {title.lower()}: {line}. Used in {used}." for i, (title, line, used) in enumerate(STEPS))
            + " Then the agent writes down what is proven. Sample receipt from the Finish Work guide, status blocked. "
            + " ".join(f"{label}: {body}" for label, body in RECEIPT))


def how_it_works(t: dict) -> str:
    w, pad = WIDTH, 32
    body = []
    y = lines(body, pad, 54, "WHAT A SKILL CHANGES", 16, t["muted"], w - 2 * pad, 22, 600) + 18
    y = lines(body, pad, y, "From “done!” to a receipt you can check", 28, t["ink"], w - 2 * pad, 36, 700) + 30
    rail_x, tx = pad + 20, pad + 58
    room = w - tx - 20
    rail_top = y
    for i, (title, line, used_in) in enumerate(STEPS):
        gate = i == len(STEPS) - 1
        cy = y - 8
        body.append(f'<circle cx="{rail_x}" cy="{cy}" r="19" fill="{t["accent_bg"] if gate else t["bg"]}" '
                    f'stroke="{t["accent"] if gate else t["ink"]}" stroke-width="2.5"/>')
        body.append(text(rail_x, cy + 7, str(i + 1), 19, t["accent"] if gate else t["ink"], 700, "middle"))
        y = lines(body, tx, y, title, 24, t["ink"], room, 30, 700) + 2
        y = lines(body, tx, y, line, 18, t["muted"], room, 24)
        names = ", ".join(n.replace(" ", "\u00a0") for n in used_in.split(", "))  # keep each name on one line
        y = lines(body, tx, y, f"in: {names}", 17, t["muted"], room, 22) + 26
        if i == len(STEPS) - 2:
            rail_end = y - 8
    out_rail = f'<line x1="{rail_x}" y1="{rail_top}" x2="{rail_x}" y2="{rail_end}" stroke="{t["edge"]}" stroke-width="3"/>'
    # arrow from the last step down to the receipt
    body.append(f'<path d="M {rail_x} {y - 30} L {rail_x} {y + 44}" fill="none" stroke="{t["edge"]}" stroke-width="3"/>')
    body.append(f'<path d="M {rail_x - 8} {y + 36} L {rail_x} {y + 50} L {rail_x + 8} {y + 36} Z" fill="{t["edge"]}"/>')
    y = lines(body, tx, y + 12, "then it writes down what is proven", 18, t["muted"], room, 24) + 34
    # receipt card with a torn bottom edge
    rx, ry, rw = pad - 8, y, w - 2 * (pad - 8)
    card = [text(rx + 20, ry + 40, "RECEIPT", 17, t["muted"], 700, family=MONO, spacing="2"),
            f'<rect x="{rx + rw - 136}" y="{ry + 16}" width="116" height="34" rx="17" fill="{t["accent_bg"]}"/>',
            text(rx + rw - 78, ry + 40, "blocked", 18, t["accent"], 700, "middle", MONO)]
    cy = ry + 86
    for label, value in RECEIPT:
        card.append(text(rx + 20, cy, label, 16, t["muted"], 700, family=MONO, spacing="1"))
        cy = lines(card, rx + 20, cy + 26, value, 16, t["ink"], rw - 40, 23, family=MONO, mono=True) + 12
    card.append(text(rx + 20, cy + 14, "sample from the Finish Work guide", 15, t["muted"], family=MONO))
    rh = cy + 40 - ry
    teeth = 18
    step = rw / teeth
    zig = " ".join(f"L {round(rx + rw - k * step, 1)} {ry + rh + (8 if k % 2 else 0)}" for k in range(1, teeth + 1))
    paper = (f'<path d="M {rx} {ry} L {rx + rw} {ry} L {rx + rw} {ry + rh} {zig} L {rx} {ry + rh} Z" '
             f'fill="{t["paper"]}" stroke="{t["paper_edge"]}" stroke-width="2" stroke-linejoin="round"/>')
    h = ry + rh + 34
    out = frame(w, h, t, "What a skill changes", HOW_DESC) + [out_rail] + body + [paper] + card + ["</svg>"]
    return "\n".join(out) + "\n"


def proof_chart(t: dict, catalog: dict) -> str:
    skills = sorted(catalog["skills"], key=lambda e: LEVELS.index(e["proof"]["level"]))
    w, pad = WIDTH, 32
    desc = " ".join(f'{e["display_name"]}: {LEVEL_NAMES[e["proof"]["level"]]}, {e["proof"]["headline"]} '
                    f'({e["proof"]["caption"]}).' for e in skills)
    body = []
    y = lines(body, pad, 54, "PROOF SO FAR", 16, t["muted"], w - 2 * pad, 22, 600) + 18
    y = lines(body, pad, y, "Every skill lists its evidence and its limits", 26, t["ink"], w - 2 * pad, 34, 700) + 14
    for n, level in enumerate(LEVELS):
        lx, ly = pad + (n % 2) * 196, y + (n // 2) * 32
        color = t["levels"][level]
        for k in range(4):
            body.append(f'<circle cx="{lx + 6 + k * 13}" cy="{ly - 6}" r="5" fill="{color if k < LEVEL_DOTS[level] else t["dot_off"]}"/>')
        body.append(text(lx + 58, ly, LEVEL_NAMES[level], 17, t["ink"], 600))
    y += 54
    body.append(f'<line x1="{pad}" y1="{y}" x2="{w - pad}" y2="{y}" stroke="{t["edge"]}" stroke-width="1.5"/>')
    y += 50
    for i, e in enumerate(skills):
        level = e["proof"]["level"]
        color = t["levels"][level]
        row = []
        row.append(text(pad, y, e["display_name"], 21, t["ink"], 700))
        row.append(text(w - pad, y, e["proof"]["headline"], 22, color, 700, "end"))
        for k in range(4):
            row.append(f'<circle cx="{w - pad - 57 + k * 17}" cy="{y + 20}" r="6" fill="{color if k < LEVEL_DOTS[level] else t["dot_off"]}"/>')
        bottom = lines(row, pad, y + 27, e["proof"]["caption"], 17, t["muted"], w - 2 * pad - 84, 22)
        if i % 2 == 0:
            body.append(f'<rect x="{pad - 14}" y="{y - 30}" width="{w - 2 * pad + 28}" height="{bottom - y + 16}" rx="10" fill="{t["card"]}"/>')
        body += row
        y = bottom + 34
    y = lines(body, pad, y + 4, "Numbers come from catalog.json and evaluations/.", 15, t["muted"], w - 2 * pad, 20)
    out = frame(w, y + 14, t, "Proof so far, by skill", desc) + body + ["</svg>"]
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
