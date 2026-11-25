#!/usr/bin/env python3
"""Settle gate for the T3 conductor. Read-only on the T3 database.

A run that ended is not a goal that is met. This checks a thread's own last
words, last run and linked pull requests for signs that its goal is still
open, before anyone settles it.

    settle_check.py ID [ID ...]            one line per thread: ALLOW or BLOCK + why
    settle_check.py --json ID [ID ...]     the same as JSON
    settle_check.py --proof "TEXT" ID      record where the goal's proof is for a
                                           BLOCKed thread, then it may be settled
    settle_check.py --hook                 PreToolUse hook mode (reads the tool call
                                           on stdin; denies an unproven settle)

Exit 0 when every thread is ALLOW, 1 when any is BLOCK.

Rules:
  - A child or helper thread is ALLOW: its report went to its parent.
  - A root thread is BLOCK when any open signal is found, unless a proof line
    newer than its last message is in the settle log.
  - BLOCK is not "never settle". It means: read the thread, then advance it
    or desk it (snooze last), or record the proof that the goal is met.

The database is $T3_STATE_DB, else ~/.t3/userdata/statev2.sqlite. The log is
$CONDUCTOR_SETTLE_LOG, else settle-log.jsonl in $CONDUCTOR_HOME, else in
./conductor. T3's database layout is not a public contract: when a table or
column is missing the check says so and the hook lets the call through.
"""
import argparse
import datetime as dt
import json
import os
import re
import sqlite3
import sys

DB = os.environ.get("T3_STATE_DB", os.path.expanduser("~/.t3/userdata/statev2.sqlite"))
LOG = os.environ.get("CONDUCTOR_SETTLE_LOG") or os.path.join(
    os.environ.get("CONDUCTOR_HOME") or "conductor", "settle-log.jsonl"
)
TAIL = 1500  # characters of the final message that are read
BAD_RUN = ("failed", "interrupted", "cancelled", "queued", "preparing", "starting", "running", "waiting")

# (label, pattern). Each is a sign the goal is still open. The patterns began as
# a fit to 165 judged settles in one live fleet (see the skill's evaluation) and
# had that fleet's names taken out. Add your own lanes' phrases here: the gate
# is only as good as this list. CONDUCTOR_OWNER_NAMES adds the owner's names
# (comma separated) to "you" in the owner patterns.
OWNER = "|".join(["you", "the owner"] + [re.escape(n.strip()) for n in
                                        os.environ.get("CONDUCTOR_OWNER_NAMES", "").split(",") if n.strip()])
SIGNALS = [
    ("out of usage", r"(?i)hit your (weekly|usage|session) limit|usage limit reached"),
    ("says blocked", r"\bBLOCKED\b|(?i:status[: ]+blocked|\bstill blocked\b|is blocked on)"),
    ("says parked or gated", r"\bPARKED\b|\bGATED\b"),
    ("asks the owner", r"(?i)\byour call\b|needs? your (yes|ok|answer|tap|approval)|still needs? your"
                       rf"|next for ({OWNER})\b|wait(s|ing)? on ({OWNER})\b"
                       r"|answer (the |that |this |one of the )?(\d )?(open )?(desk )?cards?"
                       rf"|when you answer|if you don.t answer|({OWNER}) (gives|answers|approves|runs)\b"
                       r"|approve one|paste it here"),
    ("waits on a desk card", r"(?i)card (was |is )?\*{0,2}refused|desk slot frees"
                             r"|wait(s|ing) on (those|the|that|two|both) (desk )?cards?|next desk card is up"),
    ("waits on something", r"(?i)i.m watching|until (then|it reports) i|wait(s|ing)? on the conductor|hasn.t replied"
                           r"|isn.t finished|not fixed yet|no ruling (on it )?yet|is still (a draft|running\.)"
                           r"|are still running|could not close|no final health readback"),
    ("names a next step it owes", r"(?i)next:?\*{0,2}:? (when|once) |i.ll (make|send|record|start|rebase|compare)\b"
                                  r"|i.m running it|rerun (this task|the brief|above)"
                                  r"|next for the conductor|the conductor (reads|rules)"),
    ("goal missed", r"(?i)target missed|closed as .?failed|not run; no"),
]
QUIET = re.compile(r"(?i)next:?\*{0,2}:? (nothing|none|no action)")


def utc(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def connect():
    return sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=5)


def _text(payload):
    p = json.loads(payload)
    s = p.get("text") or p.get("content") or ""
    if isinstance(s, list):
        s = " ".join(str(a.get("text", "")) if isinstance(a, dict) else str(a) for a in s)
    return re.sub(r"\s+", " ", str(s))


def proofs():
    out = {}
    try:
        with open(LOG) as f:
            for line in f:
                try:
                    r = json.loads(line)
                    if r.get("proof"):
                        out[r["thread"]] = r
                except (ValueError, KeyError):
                    continue
    except OSError:
        pass
    return out


def check(con, tid, proof_log=None):
    """Return {thread, title, kind, verdict, reasons, proof} for one thread."""
    row = con.execute(
        "select title, payload_json from orchestration_v2_projection_threads where thread_id = ?", (tid,)
    ).fetchone()
    if not row:
        return {"thread": tid, "title": None, "kind": "unknown", "verdict": "BLOCK",
                "reasons": ["thread not found in this machine's T3 database"], "proof": None}
    title, payload = row
    p = json.loads(payload)
    parent = (p.get("lineage") or {}).get("parentThreadId")
    kind = "child" if parent else ("owner" if p.get("createdBy") != "agent" else "lane")
    out = {"thread": tid, "title": title, "kind": kind, "verdict": "ALLOW", "reasons": [], "proof": None}
    if kind == "child":
        return out

    reasons = []
    run = con.execute(
        "select status from orchestration_v2_projection_runs where thread_id = ? order by ordinal desc limit 1", (tid,)
    ).fetchone()
    if run and run[0] in BAD_RUN:
        reasons.append(f"last run {run[0]}")

    last, last_at = "", None
    for role, at, pj in con.execute(
        "select role, created_at, payload_json from orchestration_v2_projection_messages "
        "where thread_id = ? and role = 'assistant' order by created_at desc limit 6", (tid,)
    ):
        t = _text(pj)
        if len(t) > 40:
            last, last_at = t[-TAIL:], at
            break
    if not last:
        reasons.append("no final message to read")
    elif not QUIET.search(last):
        for label, pat in SIGNALS:
            m = re.search(pat, last)
            if m:
                reasons.append(f"{label}: \"{last[max(0, m.start() - 30):m.end() + 40].strip()}\"")
    elif re.search(SIGNALS[0][1], last) or re.search(SIGNALS[1][1], last):
        reasons.append("says blocked or out of usage")

    for pr in p.get("pullRequests") or []:
        snap = pr.get("snapshot") or {}
        if snap.get("state") == "open":
            reasons.append(f"linked PR #{pr.get('number')} is open{' (draft)' if snap.get('isDraft') else ''}")

    if reasons:
        pr_rec = (proof_log if proof_log is not None else proofs()).get(tid)
        if pr_rec and (not last_at or utc(pr_rec["at"]) >= utc(last_at)):
            out["proof"] = pr_rec["proof"]
            out["reasons"] = reasons
            return out
        out["verdict"] = "BLOCK"
        out["reasons"] = reasons
    return out


def _now():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _append(rec):
    folder = os.path.dirname(LOG)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(LOG, "a") as f:
        f.write(json.dumps(rec) + "\n")


def record_proof(tid, text):
    con = connect()
    r = check(con, tid, proof_log={})
    rec = {"at": _now(), "thread": tid, "title": r["title"], "proof": text, "signals": r["reasons"],
           "by": os.environ.get("T3CODE_THREAD_ID", "unknown")}
    _append(rec)
    return rec


def hook():
    """PreToolUse on t3_thread_organize: deny settling a root thread that still looks open."""
    try:
        call = json.load(sys.stdin)
        i = call.get("tool_input") or {}
        if i.get("action") != "settle" or not i.get("threadId") or i.get("environmentId"):
            return 0  # not a settle, a thread settling itself, or another Mac's database
        if i["threadId"] == os.environ.get("T3CODE_THREAD_ID"):
            return 0
        r = check(connect(), i["threadId"])
        if r["kind"] in ("lane", "owner"):  # every root settle leaves a line, so the next audit is one file read
            try:
                _append({"at": _now(), "thread": i["threadId"], "title": r["title"], "gate": r["verdict"],
                         "signals": r["reasons"][:4], "proofUsed": r["proof"],
                         "by": os.environ.get("T3CODE_THREAD_ID", "unknown")})
            except OSError:  # a log that cannot be written must not turn a refusal into a pass
                pass
        if r["verdict"] != "BLOCK" or r["kind"] == "unknown":
            return 0
        why = "; ".join(r["reasons"][:4])
        me = os.path.abspath(__file__)
        reason = (
            f"SETTLE GATE: \"{(r['title'] or '')[:60]}\" still looks open ({why}). A run that ended is not a goal that is met. "
            "Read the thread, then take the first move that fits: advance it (send the next whole outcome), or put it on the "
            "desk and leave it unsnoozed. Snooze only as a last resort, for a fixed clock time. If you have read the proof that its goal is met, or its work was "
            f"handed whole to a named live thread, record that first: python3 {me} --proof \"<where the proof is>\" "
            f"'{i['threadId']}' and then settle. Helpers never record proof for a thread they did not read."
        )
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                                 "permissionDecisionReason": reason}}))
    except Exception:  # never break a tool call because the gate itself failed
        return 0
    return 0


def main():
    ap = argparse.ArgumentParser(description="Settle gate: is this T3 thread's goal still open?")
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--proof")
    ap.add_argument("--hook", action="store_true")
    a = ap.parse_args()
    if a.hook:
        return hook()
    if not a.ids:
        ap.error("give at least one thread id")
    if a.proof:
        if len(a.ids) != 1:
            ap.error("--proof takes exactly one thread id: one thread, one proof")
        if len(a.proof.strip()) < 15:
            ap.error("the proof must say where the evidence is (a path, a PR, a card, or the live thread that took the work)")
        rec = record_proof(a.ids[0], a.proof.strip())
        print(f"proof recorded for \"{rec['title']}\"; it may be settled now")
        return 0
    con, log = connect(), proofs()
    rows = [check(con, t, log) for t in a.ids]
    if a.json:
        json.dump(rows, sys.stdout, indent=1)
        print()
    else:
        for r in rows:
            tail = f" (proof on file: {r['proof'][:60]})" if r["proof"] else ""
            why = "" if not r["reasons"] or r["proof"] else " | " + "; ".join(r["reasons"][:3])
            print(f"{r['verdict']:<5} | {r['kind']:<5} | {(r['title'] or '?')[:55]}{tail}{why}")
    return 1 if any(r["verdict"] == "BLOCK" for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
