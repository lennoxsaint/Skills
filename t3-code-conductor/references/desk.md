# The desk

The desk is the owner's one review page. It holds only decisions that are truly theirs. Everything else the conductor handles or answers from the standing decisions.

## The card contract

| Field | Rule |
|---|---|
| `id` | Lowercase letters, digits and dashes. Shown on the page, so no thread ids or private names. |
| `title` | The decision as a question, up to 120 characters. "Ship the new pricing page?" |
| `why` | What it is, why it matters and what happens on each answer, up to 1,200 characters. Longer detail goes behind a link. |
| `yes` | The recommended answer, shown as the big choice. Required. |
| `no` | The other answer, if there is one. |
| `lane` | Which lane gets the answer. |
| `due` | `YYYY-MM-DD` when a deadline is real. Cards with a due date sort first. |
| `priority` | 1 (most urgent) to 5. Default 3. |
| `links` | `https://` only. Everything the owner must see has to open on a phone. |

A card approves only what it names. Name the exact action, target and version in the title or `why`: "Post these 3 clips to the shop account on Friday?", not "Approve the clips?".

Before you add a card, make it a one-tap decision: the work done, the evidence ready, the recommendation chosen.

## Commands

```bash
D=<skill-dir>/scripts/desk.py          # needs Python 3.9+
export CONDUCTOR_HOME=~/conductor       # the run folder for every command below
python3 $D init                         # once
python3 $D add c-pricing --title "Ship the new pricing page?" \
  --why "Copy and layout passed review at commit 3f2a1c9. Staging link below." \
  --yes "Ship it" --no "Hold it" --lane web --due 2026-11-20 --priority 2 \
  --link https://staging.example.com/pricing
python3 $D show                         # open cards in rank order
python3 $D lint                         # PASS, or the problems that stop a card working on a phone
python3 $D render                       # writes review.html
python3 $D answer c-pricing --choice yes --note "after the Friday call"
python3 $D routed c-pricing --lane web  # after the answer reached the lane
python3 $D close c-pricing --result "shipped and checked on the live site"
python3 $D ledger "c-pricing: owner said yes, sent to web"
```

Without `CONDUCTOR_HOME`, pass the same `--dir <run-folder>` to every command; otherwise the helper uses `./conductor` in the current folder.

Every command prints one line of JSON (`show` without `--json` prints a list). A failure prints `desk.py: <reason>` and exits 1.

## What the helper guarantees

- **One writer at a time.** Every write takes a lock in the run folder, writes a temp file, renames it into place and reads it back.
- **Nothing local reaches the phone.** `lint` refuses open cards that name a local path (`/Users/`, `/home/`, `~/`, `C:\`, `file://`), a link that is not `https://`, text over its limit, or no recommended answer. `render` refuses to run while `lint` fails.
- **Nothing remote loads.** `review.html` has inline styles, no scripts, no remote fonts or images, and every value is HTML-escaped.
- **Answers follow an order.** A card must be answered before it can be marked routed.
- **The ledger only grows.** `ledger` appends one line and turns line breaks into spaces, so one call cannot forge a second line.

## What it does not do

It does not serve the page, send anything, or watch for answers. The conductor reads the owner's reply line in T3 or chat, records it with `answer`, delivers it to the lane, then marks it `routed`. See [setup](setup.md) for ways to open the page on a phone.
