# Setup

Do this once per factory. It takes about ten minutes. After that, every conductor, lane and timer works from the same folder.

## 1. Pick the run folder

Pick a folder on the machine where the conductor thread runs. Keep it out of folders that sync to the cloud and can evict files (some "Documents" folders do). A plain folder in your home directory is fine.

```bash
export CONDUCTOR_HOME=~/conductor
python3 <skill-dir>/scripts/desk.py init
```

`init` creates the files below, except `review.html`, and never overwrites one that exists. `--dir` can go before or after the command.

| File | What it holds |
|---|---|
| `CONDUCTOR.md` | The one current conductor thread: its id, machine and model. Everything that reports to "the conductor" reads this. |
| `ROSTER.md` | One row per lane: name, thread id, machine, model, finish line, state. |
| `LEDGER.md` | Append-only log. One dated line per decision, dispatch, proof or handover. |
| `STANDING.md` | The owner's standing decisions: what the conductor may decide alone, what always needs the owner, and their stated priorities. |
| `desk.json` | The review cards. Change it only through `desk.py`. |
| `review.html` | The rendered phone page. `desk.py render` rewrites it. |

## 2. Write the standing decisions

Fill `STANDING.md` with the owner, in their words. At least:

- the ranked priorities and what "done" means for each
- what the conductor may do alone (for example: run tests, merge to a staging branch after review, answer lanes from earlier decisions)
- what always needs the owner (for example: publish, send to real people, spend, delete, merge to production, anything about taste)
- usage ceiling and time box
- which threads are the owner's own and must not be steered

This file is how the conductor answers for the owner without asking.

## 3. Start the conductor thread

Create one T3 thread for the conductor and give it the launch prompt below. Put its id in `CONDUCTOR.md`.

```text
use t3-code-conductor. you are the conductor for my T3 Code threads.
the run folder is <path>. read CONDUCTOR.md, STANDING.md, ROSTER.md and the end of LEDGER.md first.
start with a full census of every thread on every connected machine, map each open thread to a lane,
then run cycles until <finish line or time box>. keep the review page current.
```

## 4. Lanes

For each open goal with no owner, create one lane thread (batch creation if your T3 build has it). Same model and mode as the other lanes unless the owner set otherwise. Write each lane into `ROSTER.md` and the ledger. Never create a second thread for a lane that already has one.

## 5. The scheduled refresh

If your T3 build has a scheduling tool (for example `schedule_task`), add one refresh every 3 hours, bound to the conductor thread or run as a fresh session each time. Its prompt:

```text
desk refresh. read CONDUCTOR.md, STANDING.md and the end of LEDGER.md in <path>.
check only lanes that changed since the last ledger line. update cards with desk.py,
run desk.py lint, then desk.py render. if nothing changed, write nothing and stop.
never publish, send, spend or delete. one ledger line if you changed anything.
```

If there is no scheduling tool, the conductor refreshes the page at the end of each cycle. Do not build your own scheduler with a shell loop.

## 6. Getting the page to the phone

`review.html` is one self-contained file: no remote scripts, fonts or trackers. Pick one way to open it on a phone:

- open the file from a synced folder that your phone can read (and that does not evict it on the conductor's machine)
- serve the run folder on a private network only you can reach
- publish it as a private page through a tool you already trust

Never serve it on the open internet. It holds your decisions and your project names.

The owner answers by sending the card's reply line (shown on each card, for example `answer c-launch yes`) to the conductor thread from any device where they can reach T3, or by telling the conductor in chat. The conductor records it with `desk.py answer`, delivers it to the lane and marks it routed.

A faster path, if you want one later: a small watcher that wakes the conductor when an answers file changes, through a webhook trigger on the scheduling tool. Keep the 3-hour refresh as the safety net. This skill does not ship that watcher.
