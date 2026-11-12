#!/usr/bin/env python3
"""desk.py: the conductor's run folder, ledger and phone review page.

Standard library only. Every desk write takes one lock, writes a temp file,
renames it onto desk.json and reads it back, so a conductor and a scheduled
refresh never write at the same moment.

  desk.py init                       create the run folder files (never overwrites)
  desk.py ledger TEXT                append one dated line to LEDGER.md
  desk.py add ID --title T --yes Y [--why W] [--no N] [--lane L] [--due YYYY-MM-DD] [--priority P] [--link URL ...]
  desk.py answer ID --choice C [--note N]   record the owner's answer
  desk.py routed ID --lane L         the answer was delivered to its lane; the card moves to done
  desk.py close ID --result TEXT     close a card without an answer (no longer needed)
  desk.py show [--json]              open cards in rank order
  desk.py lint                       problems that would stop a card working on a phone
  desk.py render [--out FILE]        write the self-contained review.html

The run folder is --dir, else $CONDUCTOR_HOME, else ./conductor.
"""
import argparse
import datetime as dt
import html
import json
import os
import re
import sys
import tempfile
import time

LIMITS = {"title": 120, "why": 1200, "yes": 80, "no": 80, "note": 600, "lane": 60, "result": 300}
LOCAL_PATH = re.compile(r"(^|[\s\"'(=])(/Users/|/home/|~/|[A-Za-z]:\\|file://)", re.IGNORECASE)
CARD_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,47}$")
STATES = ("open", "answered", "done", "closed")

TEMPLATES = {
    "CONDUCTOR.md": "# Current conductor\n\nThread: <thread id>\nMachine: <machine>\nModel: <model>\nSince: <date>\n\nEvery lane, timer and script that reports to the conductor reads this file.\nOn a handover, change only this file and the conductor row in ROSTER.md.\n",
    "ROSTER.md": "# Roster\n\n| Lane | Thread | Machine | Model | Finish line | State |\n|---|---|---|---|---|---|\n| conductor | <thread id> | <machine> | <model> | runs the factory | active |\n",
    "LEDGER.md": "# Ledger\n\nAppend only. One dated line per decision, dispatch, proof or handover.\n\n",
    "STANDING.md": "# Standing decisions\n\n## Priorities, in order\n\n1. <outcome> - done means <evidence>\n\n## The conductor may do alone\n\n- <for example: run tests, merge to staging after an outside review>\n\n## Always needs the owner\n\n- publish, send to real people, spend, delete, change access, merge to production, taste calls\n\n## Limits\n\n- usage: wind down at 85%, stop new dispatch at 90%\n- time box: <hours>\n\n## The owner's own threads (read, never steer)\n\n- <thread ids>\n",
}


class DeskError(Exception):
    pass


def home(args):
    folder = args.dir or os.environ.get("CONDUCTOR_HOME") or "conductor"
    return os.path.abspath(os.path.expanduser(folder))


def now():
    return dt.datetime.now().astimezone()


def stamp():
    return now().strftime("%Y-%m-%d %H:%M %Z").strip()


class Lock:
    """A mkdir lock. Waits up to 30 s and breaks a lock older than 5 minutes."""

    def __init__(self, folder):
        self.path = os.path.join(folder, ".desk.lock")

    def __enter__(self):
        deadline = time.time() + 30
        while True:
            try:
                os.mkdir(self.path)
                return self
            except FileExistsError:
                try:
                    age = time.time() - os.path.getmtime(self.path)
                except FileNotFoundError:
                    continue
                if age > 300:
                    try:
                        os.rmdir(self.path)
                    except OSError:
                        pass
                    print("desk.py: broke a lock older than 5 minutes", file=sys.stderr)
                    continue
                if time.time() > deadline:
                    raise DeskError("desk is locked by another writer; try again")
                time.sleep(0.05)

    def __exit__(self, *exc):
        try:
            os.rmdir(self.path)
        except OSError:
            pass


def desk_path(folder):
    return os.path.join(folder, "desk.json")


def load(folder):
    path = desk_path(folder)
    if not os.path.exists(path):
        raise DeskError(f"no desk at {path}; run `desk.py init` first")
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict) or not isinstance(data.get("cards"), dict):
        raise DeskError("desk.json must hold {\"cards\": {...}}")
    return data


def save(folder, data):
    path = desk_path(folder)
    fd, temp = tempfile.mkstemp(prefix=".desk-", suffix=".json", dir=folder)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)
    with open(path, encoding="utf-8") as handle:
        if json.load(handle) != data:
            raise DeskError("desk.json read back different from what was written")


def check_length(field, value):
    if value is not None and len(value) > LIMITS[field]:
        raise DeskError(f"{field} is {len(value)} characters; the limit is {LIMITS[field]}")


def mutate(folder, change):
    with Lock(folder):
        data = load(folder)
        result = change(data)
        data["updated"] = now().isoformat(timespec="seconds")
        save(folder, data)
    return result


def get_card(data, card_id):
    card = data["cards"].get(card_id)
    if card is None:
        raise DeskError(f"no card {card_id!r}")
    return card


def cmd_init(args):
    folder = home(args)
    os.makedirs(folder, exist_ok=True)
    made = []
    for name, text in TEMPLATES.items():
        path = os.path.join(folder, name)
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(text)
            made.append(name)
    if not os.path.exists(desk_path(folder)):
        with Lock(folder):
            save(folder, {"cards": {}, "updated": now().isoformat(timespec="seconds")})
        made.append("desk.json")
    return {"folder": folder, "created": made}


def cmd_ledger(args):
    folder = home(args)
    text = " ".join(args.text).replace("\n", " ").strip()
    if not text:
        raise DeskError("ledger text is empty")
    path = os.path.join(folder, "LEDGER.md")
    if not os.path.exists(path):
        raise DeskError(f"no ledger at {path}; run `desk.py init` first")
    with Lock(folder):
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(f"- {stamp()} {text}\n")
    return {"ledger": path, "line": text}


def cmd_add(args):
    if not CARD_ID.match(args.id):
        raise DeskError("card id: lowercase letters, digits and dashes, up to 48 characters")
    for field in ("title", "why", "yes", "no", "lane"):
        check_length(field, getattr(args, field))
    if args.due:
        try:
            dt.date.fromisoformat(args.due)
        except ValueError as error:
            raise DeskError("--due must be YYYY-MM-DD") from error

    def change(data):
        if args.id in data["cards"]:
            raise DeskError(f"card {args.id!r} already exists")
        data["cards"][args.id] = {
            "title": args.title, "why": args.why or "", "yes": args.yes, "no": args.no or "",
            "lane": args.lane or "", "due": args.due or "", "priority": args.priority,
            "links": args.link or [], "state": "open", "created": now().isoformat(timespec="seconds"),
        }
        return {"added": args.id}

    return mutate(home(args), change)


def cmd_answer(args):
    check_length("note", args.note)

    def change(data):
        card = get_card(data, args.id)
        if card["state"] not in ("open", "answered"):
            raise DeskError(f"card {args.id!r} is {card['state']}; it takes no answer")
        card.update(state="answered", choice=args.choice, note=args.note or "",
                    answered=now().isoformat(timespec="seconds"))
        return {"answered": args.id, "choice": args.choice}

    return mutate(home(args), change)


def cmd_routed(args):
    check_length("lane", args.lane)

    def change(data):
        card = get_card(data, args.id)
        if card["state"] != "answered":
            raise DeskError(f"card {args.id!r} is {card['state']}; record the answer before routing it")
        card.update(state="done", routed_to=args.lane, routed=now().isoformat(timespec="seconds"))
        return {"routed": args.id, "lane": args.lane}

    return mutate(home(args), change)


def cmd_close(args):
    check_length("result", args.result)

    def change(data):
        card = get_card(data, args.id)
        card.update(state="closed", result=args.result, closed=now().isoformat(timespec="seconds"))
        return {"closed": args.id}

    return mutate(home(args), change)


def ranked(cards, state="open"):
    rows = [(card_id, card) for card_id, card in cards.items() if card.get("state") == state]
    return sorted(rows, key=lambda row: (row[1].get("due") or "9999-12-31", row[1].get("priority", 3), row[1].get("created", ""), row[0]))


def cmd_show(args):
    data = load(home(args))
    rows = ranked(data["cards"])
    if args.json:
        return [{"id": card_id, **card} for card_id, card in rows]
    for card_id, card in rows:
        due = f" due {card['due']}" if card.get("due") else ""
        print(f"{card_id}  P{card.get('priority', 3)}{due}  {card['title']}  -> {card.get('lane') or 'no lane'}")
    print(f"{len(rows)} open")
    return None


def lint_cards(data):
    problems = []
    for card_id, card in data["cards"].items():
        if card.get("state") != "open":
            continue
        visible = [card.get(field, "") for field in ("title", "why", "yes", "no")] + list(card.get("links", []))
        for value in visible:
            if LOCAL_PATH.search(value or ""):
                problems.append(f"{card_id}: names a local path a phone cannot open: {value[:60]!r}")
        for link in card.get("links", []):
            if not link.startswith("https://"):
                problems.append(f"{card_id}: link must start with https://: {link[:60]!r}")
        for field, limit in LIMITS.items():
            if len(card.get(field, "") or "") > limit:
                problems.append(f"{card_id}: {field} is over {limit} characters")
        if not card.get("yes"):
            problems.append(f"{card_id}: has no recommended answer")
    return problems


def cmd_lint(args):
    problems = lint_cards(load(home(args)))
    for problem in problems:
        print(problem)
    print("PASS" if not problems else f"FAIL: {len(problems)} problem(s)")
    return 0 if not problems else 1


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>Review desk</title>
<style>
:root {{ --bg:#f7f7f5; --card:#fff; --ink:#1b1b1b; --muted:#666; --line:#e2e2de; --go:#16794a; --due:#b4232a; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#141414; --card:#1f1f1f; --ink:#f2f2f2; --muted:#a8a8a8; --line:#333; --go:#3fb27f; --due:#ff6b6b; }} }}
* {{ box-sizing:border-box; }}
body {{ margin:0; padding:16px; background:var(--bg); color:var(--ink); font:16px/1.45 -apple-system, system-ui, sans-serif; }}
main {{ max-width:640px; margin:0 auto; }}
h1 {{ font-size:22px; margin:4px 0 2px; }} h2 {{ font-size:15px; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); margin:28px 0 8px; }}
.meta, .small {{ color:var(--muted); font-size:13px; }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:14px; margin:10px 0; }}
.card h3 {{ font-size:17px; margin:0 0 6px; }}
.due {{ color:var(--due); font-weight:600; font-size:13px; }}
.why {{ white-space:pre-wrap; margin:6px 0 10px; }}
.yes {{ display:block; background:var(--go); color:#fff; border-radius:10px; padding:12px; font-weight:600; text-align:center; }}
.no {{ display:block; text-align:center; padding:8px; color:var(--muted); }}
code {{ display:block; overflow-wrap:anywhere; background:var(--bg); border:1px solid var(--line); border-radius:8px; padding:8px; margin-top:8px; font-size:14px; }}
a {{ color:inherit; }}
</style></head><body><main>
<h1>{headline}</h1>
<p class="meta">Updated {updated}. Send a reply line to the conductor to answer a card.</p>
<h2>Needs you ({open_count})</h2>
{open_cards}
<h2>Answered, on the way to its lane ({answered_count})</h2>
{answered_cards}
<h2>Done ({done_count})</h2>
{done_cards}
</main></body></html>
"""


def esc(value):
    return html.escape(str(value or ""), quote=True)


def render_open(card_id, card):
    due = f'<div class="due">Due {esc(card["due"])}</div>' if card.get("due") else ""
    why = f'<div class="why">{esc(card["why"])}</div>' if card.get("why") else ""
    links = "".join(f'<div class="small"><a href="{esc(link)}" rel="noopener noreferrer">{esc(link)}</a></div>' for link in card.get("links", []))
    no = f'<div class="no">or: {esc(card["no"])} <code>answer {esc(card_id)} no</code></div>' if card.get("no") else ""
    lane = f' &middot; goes to {esc(card["lane"])}' if card.get("lane") else ""
    return (f'<section class="card" id="{esc(card_id)}"><h3>{esc(card["title"])}</h3>{due}{why}{links}'
            f'<div class="yes">{esc(card["yes"])}</div><code>answer {esc(card_id)} yes</code>{no}'
            f'<div class="small">{esc(card_id)}{lane}</div></section>')


def render_answered(card_id, card):
    note = f' &middot; {esc(card["note"])}' if card.get("note") else ""
    return f'<section class="card"><h3>{esc(card["title"])}</h3><div class="small">You said {esc(card.get("choice"))}{note}</div></section>'


def render_done(card_id, card):
    if card.get("state") == "done":
        line = f'Sent to {esc(card.get("routed_to"))}'
    else:
        line = f'Closed: {esc(card.get("result"))}'
    return f'<section class="card"><h3>{esc(card["title"])}</h3><div class="small">{line}</div></section>'


def cmd_render(args):
    folder = home(args)
    data = load(folder)
    problems = lint_cards(data)
    if problems:
        raise DeskError("lint failed; fix these before rendering:\n" + "\n".join(problems))
    open_rows = ranked(data["cards"])
    answered = ranked(data["cards"], "answered")
    finished = [(card_id, card) for card_id, card in data["cards"].items() if card.get("state") in ("done", "closed")]
    finished.sort(key=lambda row: row[1].get("routed") or row[1].get("closed") or "", reverse=True)
    finished = finished[:20]
    empty = '<p class="small">Nothing here.</p>'
    page = PAGE.format(
        headline="Nothing needs you" if not open_rows else f"{len(open_rows)} decision{'s' if len(open_rows) != 1 else ''} need{'s' if len(open_rows) == 1 else ''} you",
        updated=esc(stamp()),
        open_count=len(open_rows), answered_count=len(answered), done_count=len(finished),
        open_cards="".join(render_open(*row) for row in open_rows) or empty,
        answered_cards="".join(render_answered(*row) for row in answered) or empty,
        done_cards="".join(render_done(*row) for row in finished) or empty,
    )
    out = args.out or os.path.join(folder, "review.html")
    fd, temp = tempfile.mkstemp(prefix=".review-", suffix=".html", dir=os.path.dirname(os.path.abspath(out)))
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(page)
    os.replace(temp, out)
    return {"rendered": out, "open": len(open_rows)}


def parser():
    top = argparse.ArgumentParser(description="The conductor's run folder, ledger and phone review page.")
    top.add_argument("--dir", help="run folder (default: $CONDUCTOR_HOME, else ./conductor)")
    # --dir also works after the command: `desk.py init --dir run`.
    where = argparse.ArgumentParser(add_help=False)
    where.add_argument("--dir", default=argparse.SUPPRESS, help="run folder")
    sub = top.add_subparsers(dest="command", required=True)
    sub.add_parser("init", parents=[where])
    ledger = sub.add_parser("ledger", parents=[where])
    ledger.add_argument("text", nargs="+")
    add = sub.add_parser("add", parents=[where])
    add.add_argument("id")
    add.add_argument("--title", required=True)
    add.add_argument("--yes", required=True, help="the recommended answer, shown as the big choice")
    add.add_argument("--why")
    add.add_argument("--no")
    add.add_argument("--lane")
    add.add_argument("--due")
    add.add_argument("--priority", type=int, default=3, choices=range(1, 6))
    add.add_argument("--link", action="append")
    answer = sub.add_parser("answer", parents=[where])
    answer.add_argument("id")
    answer.add_argument("--choice", required=True)
    answer.add_argument("--note")
    routed = sub.add_parser("routed", parents=[where])
    routed.add_argument("id")
    routed.add_argument("--lane", required=True)
    close = sub.add_parser("close", parents=[where])
    close.add_argument("id")
    close.add_argument("--result", required=True)
    show = sub.add_parser("show", parents=[where])
    show.add_argument("--json", action="store_true")
    sub.add_parser("lint", parents=[where])
    render = sub.add_parser("render", parents=[where])
    render.add_argument("--out")
    return top


COMMANDS = {
    "init": cmd_init, "ledger": cmd_ledger, "add": cmd_add, "answer": cmd_answer, "routed": cmd_routed,
    "close": cmd_close, "show": cmd_show, "lint": cmd_lint, "render": cmd_render,
}


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        result = COMMANDS[args.command](args)
    except (DeskError, OSError, json.JSONDecodeError) as error:
        print(f"desk.py: {error}", file=sys.stderr)
        return 1
    if isinstance(result, int):
        return result
    if result is not None:
        print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
