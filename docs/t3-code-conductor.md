# T3 Code Conductor

T3 Code Conductor turns one T3 Code thread into the conductor of all your others.

It counts every thread on every machine T3 can reach, keeps a roster and an append-only ledger, gives each lane a whole outcome, gets an outside review on a different model before anything counts, and answers lane questions from your standing decisions. Only the decisions that are yours reach you, as cards on one review page you can read on your phone.

## When it runs

It runs when you ask for it:

- "be my T3 conductor"
- "conduct my T3 threads"
- "run my T3 agents as me"
- "set up a review desk for my agents"

It is for many threads at once. For one task, just ask for the task. If you use Claude Code without T3, use [Claude Conductor](claude-conductor.md).

## How it works

1. **One conductor.** One thread holds the role. Its id lives in `CONDUCTOR.md`, so every lane and timer knows who to report to.
2. **Census first.** Every open thread gets a lane, a closed state, an "owner's own" label (read, never steered) or a named gap. The count of open threads with nothing is zero before ranking starts.
3. **Whole outcomes.** Each lane gets the full job in one brief: the result, the facts, what it may use, the finish line and the proof that will be checked.
4. **Outside review.** The thread that built something never grades it. A fresh reviewer on a different model checks the exact commit. Any change after that needs a new review.
5. **Answer before asking.** When a lane asks something, the conductor checks your standing decisions and the ledger first. It only asks you when the call is yours.
6. **One phone page.** Each card is one decision with the recommended answer as the big choice. You reply `answer <card> yes`. The page refreshes on a schedule and after any change.

## The review page

`scripts/desk.py` keeps the cards, checks them and renders `review.html`. The conductor runs it for you; to try it yourself after installing for Claude Code (for Codex, swap `~/.claude` for `~/.codex`):

```bash
DESK=~/.claude/skills/t3-code-conductor/scripts/desk.py
python3 $DESK --dir ~/conductor init
python3 $DESK --dir ~/conductor add c-pricing --title "Ship the new pricing page?" \
  --why "Passed outside review at commit 3f2a1c9." \
  --yes "Ship it" --no "Hold it" --lane web --link https://staging.example.com/pricing
python3 $DESK --dir ~/conductor lint && python3 $DESK --dir ~/conductor render
```

The page lands at `~/conductor/review.html`. Set `CONDUCTOR_HOME=~/conductor` once and you can drop `--dir`.

The page has no scripts and loads nothing from the internet. `lint` refuses local file paths, non-https links and cards with no recommended answer, so nothing on the page only works on your computer. It is plain Python 3.9+ with no packages.

The page is a file. Getting it to your phone is up to you: a private file sync, or a private page on a host you already use. Never put it on the open internet. [`references/setup.md`](../t3-code-conductor/references/setup.md) has the options.

## What it will not do

It will not publish, send to real people, spend, delete, merge to production or change access unless you named that exact action. A tap on a card approves only what that card names. It waits for lanes to finish. It does not poll, and it never sends a bare "status?".

## Install

```bash
git clone --depth 1 https://github.com/lennoxsaint/Skills.git
python3 Skills/scripts/skills.py install t3-code-conductor --host claude
```

Use `--host codex` if your T3 conductor thread runs on Codex, or `--host both` for both. Start a new thread if the skill does not show up right away.

Then, in a fresh T3 thread, try:

```text
Use t3-code-conductor: be my conductor. Take a census of every T3 thread, give each lane a whole outcome, and keep one phone review page of what needs me.
```

## What you need

- T3 Code, with its thread tools (list, read, send, wait) and `delegate_task` for outside reviewers. A scheduling tool is optional: without it, the page refreshes when you ask.
- Python 3.9+ for `desk.py`.
- A short `STANDING.md`: your goals in order, what the conductor may do alone, and what always needs you. `desk.py init` writes a template.

## Files in the skill

| File | What it is |
|---|---|
| `SKILL.md` | The ground rules, census, lanes, review, the phone page, proof, handover |
| `references/setup.md` | The run folder, standing decisions, launch prompt, scheduled refresh, phone options |
| `references/cycle.md` | One pass step by step, the brief template, the review stack, handover |
| `references/desk.md` | The card contract and every `desk.py` command |
| `scripts/desk.py` | The review page helper |

A synthetic example lives in [`examples/t3-code-conductor/`](../examples/t3-code-conductor/sample-factory.md). The test evidence is in the [evaluation](../evaluations/t3-code-conductor.md).

## Changelog

**1.0.0** (12 Nov 2026) - first public release. This is the method I run my T3 Code threads with, written up as a skill for the first time, with my machines, accounts, thread ids and private rules taken out. The review page helper is new and tested. After a test with an agent that had never seen the skill, the text now says what to do with a "completed" thread that has no proof, an existing thread with no lane, an unreadable thread, earlier ledger lines, an unknown conductor id and non-code briefs, and that a decision still waiting on review stays off the page.
