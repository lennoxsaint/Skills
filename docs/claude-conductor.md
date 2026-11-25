# Claude Conductor

Claude Conductor runs the Claude Code threads you already have, as you.

You give it one run contract: your goals in order, what counts as done, what it may and may not do, and when to stop. It counts every open thread, keeps a ranked ledger, gives each thread's owner the whole outcome in one message, checks the real proof, and ends with one private review page.

## When it runs

It runs when you ask for it:

- "conduct my Claude sessions"
- "run my projects as me"
- "move every open thread forward"
- "check on all my agents and finish what's open"

It is for many threads at once. For one task in one session, just ask for the task. If you run your agents in T3 Code, use [T3 Code Conductor](t3-code-conductor.md).

## How a run works

1. **Take the contract.** Your prompt is the contract. It pulls out the goals, the finish lines, the authority and the stop time. It does not start a new interview.
2. **Count every thread.** Open, waiting, idle, running and resolved, in every project it can reach. A thread it cannot open is named as a gap, not skipped.
3. **Rank.** Your goals first, then threads waiting on you, then stuck work, then the rest.
4. **Hand over whole outcomes.** Each thread that owns work gets the full path in one message: reproduce, fix, show it failing then passing, an independent review, the checks, the merge you allowed, then the real result.
5. **Check the proof.** A sent message, a cleared badge or a "done!" is not proof. It reads the diff, the check run, the file or the provider's own readback.
6. **Finish honestly.** One private review page: each goal, what was really finished, the proof, every thread's state, and the decisions only you can make.

## What it will not do

It will not publish, post, send to real people, schedule, spend, delete or change access unless your contract names that exact action. A broad "act as me" does not count. When something is refused, it does not try again through another tool or account. It writes down the exact decision for you and keeps going on the rest.

It waits for threads to finish. It does not poll on a timer.

## Install

```bash
git clone --depth 1 https://github.com/lennoxsaint/Skills.git
python3 Skills/scripts/skills.py install claude-conductor --host claude
```

Use `--host codex` for Codex, or `--host both` for both. Start a new session if the skill does not show up right away.

Then fill in the launch prompt in [`references/launch-prompt.md`](../claude-conductor/references/launch-prompt.md) and paste it, or try:

```text
Use claude-conductor: count every open thread in my projects, rank them against my goals, and move each one to a proven finish.
```

## What you need

- Claude Code.
- A way for the agent to read your sessions: a thread or session tool in your runtime, or a browser it can use. The skill proves one real read before it relies on a route.
- Your goals in order, with what "done" means for each. The run is only as good as the contract.

## Files in the skill

| File | What it is |
|---|---|
| `SKILL.md` | The contract, the census, whole outcomes, authority, proof, finishing |
| `references/operations.md` | The run folder, cycles, stuck threads, sign-ins, usage limits, the review page |
| `references/launch-prompt.md` | A fill-in launch prompt |

A synthetic example lives in [`examples/claude-conductor/`](../examples/claude-conductor/sample-run.md). The test evidence is in the [evaluation](../evaluations/claude-conductor.md).

## Changelog

**1.2.2** (26 Nov 2026) - snooze is the last resort. The sweep takes the first move that fits: resolve on a proven end objective, progress, review page, and only then snooze, for a fixed clock time. Wording only; not measured.

**1.2.1** (21 Nov 2026) - read before you resolve. A top-level thread is resolved one at a time, after its last message, last run and linked pull requests are read; helpers bulk-resolve children only, and there are no "resolve all" cards. An audit of one live fleet found 45 of 165 top-level threads resolved over three days were still open.

**1.2.0** (18 Nov 2026) - sweep on the clock. At the start of any turn, when the last `SWEEP` ledger line is more than 45 minutes old, the conductor sweeps every ended thread before it handles the message, child and helper threads included. In a live fleet the 1.1.0 trigger ("sweep whenever no reply needs you") never fired: replies reached the conductor every 1.5 minutes (median over 27 hours), context compaction dropped the duty from its summary within a few hours, and sweeps ran only when the owner asked.

**1.1.0** (17 Nov 2026) - settle on the goal, not the run. When a thread's run ends, the conductor judges it against the goal it was first given: it marks a finished thread resolved, sends the next step at once when it may, or puts it on the review page with the goal, a dated list of what was achieved and what is left.

**1.0.0** (12 Nov 2026) - first public release. This is the conductor I run on my own Claude Code threads, with my machines, accounts, thread names and private rules taken out. After a test with an agent that had never seen the skill, seven lines were made clearer: what to do with an action the contract neither allows nor forbids, how to rank threads, who arranges the independent review, what to tell a thread that waits on a protected action, how to judge a stale "running" badge, the full list of thread states, and where the cycle cursor lives.
