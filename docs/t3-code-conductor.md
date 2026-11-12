# T3 Code Conductor

t3 code conductor turns one T3 Code thread into the conductor of all your others.

it counts every thread on every machine T3 can reach, keeps a roster and an append-only ledger, gives each lane a whole outcome, gets an outside review on a different model before anything counts, and answers lane questions from your standing decisions. only the decisions that are truly yours reach you, as cards on one review page you can read on your phone.

## when it runs

it runs when you ask for it:

- "be my T3 conductor"
- "conduct my T3 threads"
- "run my T3 agents as me"
- "set up a review desk for my agents"

it is for many threads at once. for one task, just ask for the task. if you use Claude Code without T3, use [Claude Conductor](claude-conductor.md).

## how it works

1. **one conductor.** one thread holds the role. its id lives in `CONDUCTOR.md`, so every lane and timer knows who to report to.
2. **census first.** every open thread gets a lane, a closed state, an "owner's own" label (read, never steered) or a named gap. the count of open threads with nothing is zero before ranking starts.
3. **whole outcomes.** each lane gets the full job in one brief: the result, the facts, what it may use, the finish line and the proof that will be checked.
4. **outside review.** the thread that built something never grades it. a fresh reviewer on a different model checks the exact commit. any change after that needs a new review.
5. **answer before asking.** when a lane asks something, the conductor checks your standing decisions and the ledger first. it only asks you when the call is truly yours.
6. **one phone page.** each card is one decision with the recommended answer as the big choice. you reply `answer <card> yes`. the page refreshes on a schedule and after any change.

## the review page

`scripts/desk.py` keeps the cards, checks them and renders `review.html`. the conductor runs it for you; to try it yourself after installing for Claude Code (for Codex, swap `~/.claude` for `~/.codex`):

```bash
DESK=~/.claude/skills/t3-code-conductor/scripts/desk.py
python3 $DESK --dir ~/conductor init
python3 $DESK --dir ~/conductor add c-pricing --title "Ship the new pricing page?" \
  --why "Passed outside review at commit 3f2a1c9." \
  --yes "Ship it" --no "Hold it" --lane web --link https://staging.example.com/pricing
python3 $DESK --dir ~/conductor lint && python3 $DESK --dir ~/conductor render
```

the page lands at `~/conductor/review.html`. set `CONDUCTOR_HOME=~/conductor` once and you can drop `--dir`.

the page has no scripts and loads nothing from the internet. `lint` refuses local file paths, non-https links and cards with no recommended answer, so nothing on the page only works on your computer. it is plain Python 3.9+ with no packages.

the page is a file. getting it to your phone is up to you: a private file sync, or a private page on a host you already use. never put it on the open internet. [`references/setup.md`](../t3-code-conductor/references/setup.md) has the options.

## what it will not do

it will not publish, send to real people, spend, delete, merge to production or change access unless you named that exact action. a tap on a card approves only what that card names. it waits for lanes to finish. it does not poll, and it never sends a bare "status?".

## install

```bash
git clone --depth 1 https://github.com/lennoxsaint/Skills.git
python3 Skills/scripts/skills.py install t3-code-conductor --host claude
```

use `--host codex` if your T3 conductor thread runs on Codex, or `--host both` for both. start a new thread if the skill does not show up right away.

then, in a fresh T3 thread, try:

```text
Use t3-code-conductor: be my conductor. Take a census of every T3 thread, give each lane a whole outcome, and keep one phone review page of what needs me.
```

## what you need

- T3 Code, with its thread tools (list, read, send, wait) and `delegate_task` for outside reviewers. a scheduling tool is optional: without it, the page refreshes when you ask.
- Python 3.9+ for `desk.py`.
- a short `STANDING.md`: your goals in order, what the conductor may do alone, and what always needs you. `desk.py init` writes a template.

## files in the skill

| file | what it is |
|---|---|
| `SKILL.md` | the ground rules, census, lanes, review, the phone page, proof, handover |
| `references/setup.md` | the run folder, standing decisions, launch prompt, scheduled refresh, phone options |
| `references/cycle.md` | one pass step by step, the brief template, the review stack, handover |
| `references/desk.md` | the card contract and every `desk.py` command |
| `scripts/desk.py` | the review page helper |

a synthetic example lives in [`examples/t3-code-conductor/`](../examples/t3-code-conductor/sample-factory.md). the test evidence is in the [evaluation](../evaluations/t3-code-conductor.md).

## changelog

**1.0.0** (12 Nov 2026) - first public release. this is the method i run my T3 Code threads with, written up as a skill for the first time, with my machines, accounts, thread ids and private rules taken out. the review page helper is new and tested. after a test with an agent that had never seen the skill, the text now says what to do with a "completed" thread that has no proof, an existing thread with no lane, an unreadable thread, earlier ledger lines, an unknown conductor id and non-code briefs, and that a decision still waiting on review stays off the page.
