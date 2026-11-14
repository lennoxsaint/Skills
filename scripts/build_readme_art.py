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
    ("Get a second opinion", "a second AI, usually another model, scores it", "Ambitious, Hill Climb, Adversarial Review"),
    ("Wait for your yes", "before it sends, posts, buys or deploys", "every skill"),
]

RECEIPT = [
    ("Asked", ["update the prices and publish them"]),
    ("True now", ["prices saved locally. not published:", "the publish token is missing."]),
    ("Checked", ["./publish.sh: exit 1, token not set"]),
    ("Next", ["get the token, then run ./publish.sh"]),
]

# Both diagrams are tall and narrow so their text stays readable on a 390 px phone.
WIDTH = 560


def text(x, y, body, size, fill, weight=400, anchor="start", family=SANS, spacing=None):
    extra = f' letter-spacing="{spacing}"' if spacing else ""
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}"{extra}>{escape(body)}</text>')


def frame(w, h, t, title, desc):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d">',
            f'<title id="t">{escape(title)}</title>', f'<desc id="d">{escape(desc)}</desc>',
            f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="20" fill="{t["bg"]}" stroke="{t["edge"]}" stroke-width="2"/>']


def how_it_works(t: dict) -> str:
    rail_x, top, gap = 60, 210, 110
    ry, rh = top + gap * 3 + 130, 400
    w, h = WIDTH, ry + rh + 36
    out = frame(w, h, t, "What a skill changes",
                "Four steps a skill adds to how your agent works: do the work, check it for real, get a second "
                "opinion from a second AI, usually a different model, and wait for your yes before anything goes out. "
                "It ends with a receipt. The sample receipt says the status is blocked: prices saved locally, "
                "not published because the publish token is missing.")
    out += [text(40, 58, "WHAT A SKILL CHANGES", 16, t["muted"], 600, spacing="1.5"),
            text(40, 100, "From “done!” to a receipt", 30, t["ink"], 700),
            text(40, 138, "you can check", 30, t["ink"], 700)]
    out.append(f'<line x1="{rail_x}" y1="{top}" x2="{rail_x}" y2="{top + gap * 3}" stroke="{t["edge"]}" stroke-width="3"/>')
    for i, (title, line, used_in) in enumerate(STEPS):
        y = top + gap * i
        gate = i == len(STEPS) - 1
        out.append(f'<circle cx="{rail_x}" cy="{y}" r="20" fill="{t["accent_bg"] if gate else t["bg"]}" '
                   f'stroke="{t["accent"] if gate else t["ink"]}" stroke-width="2.5"/>')
        out.append(text(rail_x, y + 7, str(i + 1), 19, t["accent"] if gate else t["ink"], 700, "middle"))
        out.append(text(rail_x + 40, y + 8, title, 26, t["ink"], 700))
        out.append(text(rail_x + 40, y + 36, line, 18, t["muted"]))
        out.append(text(rail_x + 40, y + 60, f"in: {used_in}", 16, t["muted"]))
    # arrow from the last step down to the receipt
    ay = top + gap * 3
    out.append(f'<path d="M {rail_x} {ay + 20} L {rail_x} {ay + 112}" fill="none" stroke="{t["edge"]}" stroke-width="3"/>')
    out.append(f'<path d="M {rail_x - 8} {ay + 104} L {rail_x} {ay + 118} L {rail_x + 8} {ay + 104} Z" fill="{t["edge"]}"/>')
    out.append(text(rail_x + 40, ay + 96, "then it writes down what is proven", 17, t["muted"]))
    # receipt card with a torn bottom edge
    rx, rw = 40, w - 80
    teeth = 22
    step = rw / teeth
    zig = " ".join(f"L {round(rx + rw - k * step, 1)} {ry + rh + (8 if k % 2 else 0)}" for k in range(1, teeth + 1))
    out.append(f'<path d="M {rx} {ry} L {rx + rw} {ry} L {rx + rw} {ry + rh} {zig} L {rx} {ry + rh} Z" '
               f'fill="{t["paper"]}" stroke="{t["paper_edge"]}" stroke-width="2" stroke-linejoin="round"/>')
    out.append(text(rx + 24, ry + 42, "RECEIPT", 17, t["muted"], 700, family=MONO, spacing="2"))
    out.append(f'<rect x="{rx + rw - 152}" y="{ry + 18}" width="128" height="34" rx="17" fill="{t["accent_bg"]}"/>')
    out.append(text(rx + rw - 88, ry + 42, "blocked", 18, t["accent"], 700, "middle", MONO))
    y = ry + 90
    for label, lines in RECEIPT:
        out.append(text(rx + 24, y, label, 15, t["muted"], 700, family=MONO, spacing="1"))
        y += 25
        for line in lines:
            out.append(text(rx + 24, y, line, 17, t["ink"], 400, family=MONO))
            y += 24
        y += 14
    out.append(text(rx + 24, ry + rh - 16, "sample from the Finish Work guide", 14, t["muted"], 400, family=MONO))
    out.append("</svg>")
    return "\n".join(out) + "\n"


def proof_chart(t: dict, catalog: dict) -> str:
    skills = sorted(catalog["skills"], key=lambda e: LEVELS.index(e["proof"]["level"]))
    w, row, top = WIDTH, 76, 280
    h = top + row * len(skills) + 30
    desc = " ".join(f'{e["display_name"]}: {LEVEL_NAMES[e["proof"]["level"]]}, {e["proof"]["headline"]} '
                    f'({e["proof"]["caption"]}).' for e in skills)
    out = frame(w, h, t, "Proof so far, by skill", desc)
    out += [text(40, 58, "PROOF SO FAR", 16, t["muted"], 600, spacing="1.5"),
            text(40, 98, "Every skill lists its evidence", 28, t["ink"], 700),
            text(40, 134, "and its limits", 28, t["ink"], 700)]
    for n, level in enumerate(LEVELS):
        lx, ly = 40 + (n % 2) * 250, 176 + (n // 2) * 32
        color = t["levels"][level]
        for k in range(4):
            out.append(f'<circle cx="{lx + 6 + k * 13}" cy="{ly - 5}" r="5" fill="{color if k < LEVEL_DOTS[level] else t["dot_off"]}"/>')
        out.append(text(lx + 58, ly, LEVEL_NAMES[level], 17, t["ink"], 600))
    out.append(f'<line x1="40" y1="{top - 52}" x2="{w - 40}" y2="{top - 52}" stroke="{t["edge"]}" stroke-width="1.5"/>')
    for i, e in enumerate(skills):
        y = top + row * i
        level = e["proof"]["level"]
        color = t["levels"][level]
        if i % 2 == 0:
            out.append(f'<rect x="24" y="{y - 32}" width="{w - 48}" height="{row - 4}" rx="10" fill="{t["card"]}"/>')
        out.append(text(40, y, e["display_name"], 22, t["ink"], 700))
        out.append(text(w - 40, y, e["proof"]["headline"], 24, color, 700, "end"))
        out.append(text(40, y + 27, e["proof"]["caption"], 17, t["muted"]))
        for k in range(4):
            out.append(f'<circle cx="{w - 98 + k * 17}" cy="{y + 21}" r="6" fill="{color if k < LEVEL_DOTS[level] else t["dot_off"]}"/>')
    out.append(text(40, h - 22, "Numbers come from catalog.json and evaluations/.", 15, t["muted"]))
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
