# Claude Conductor

claude conductor runs the Claude Code threads you already have, as you.

you give it one run contract: your goals in order, what counts as done, what it may and may not do, and when to stop. it counts every open thread, keeps a ranked ledger, gives each thread's owner the whole outcome in one message, checks the real proof, and ends with one private review page.

## when it runs

it runs when you ask for it:

- "conduct my Claude sessions"
- "run my projects as me"
- "move every open thread forward"
- "check on all my agents and finish what's open"

it is for many threads at once. for one task in one session, just ask for the task. if you run your agents in T3 Code, use [T3 Code Conductor](t3-code-conductor.md).

## how a run works

1. **take the contract.** your prompt is the contract. it pulls out the goals, the finish lines, the authority and the stop time. it does not start a new interview.
2. **count every thread.** open, waiting, idle, running and resolved, in every project it can reach. a thread it cannot open is named as a gap, not skipped.
3. **rank.** your goals first, then threads waiting on you, then stuck work, then the rest.
4. **hand over whole outcomes.** each thread that owns work gets the full path in one message: reproduce, fix, show it failing then passing, an independent review, the checks, the merge you allowed, then the real result.
5. **check the proof.** a sent message, a cleared badge or a "done!" is not proof. it reads the diff, the check run, the file or the provider's own readback.
6. **finish honestly.** one private review page: each goal, what was really finished, the proof, every thread's state, and the decisions only you can make.

## what it will not do

it will not publish, post, send to real people, schedule, spend, delete or change access unless your contract names that exact action. a broad "act as me" does not count. when something is refused, it does not try again through another tool or account. it writes down the exact decision for you and keeps going on the rest.

it waits for threads to finish. it does not poll on a timer.

## install

```bash
git clone --depth 1 https://github.com/lennoxsaint/Skills.git
python3 Skills/scripts/skills.py install claude-conductor --host claude
```

use `--host codex` for Codex, or `--host both` for both. start a new session if the skill does not show up right away.

then fill in the launch prompt in [`references/launch-prompt.md`](../claude-conductor/references/launch-prompt.md) and paste it, or try:

```text
Use claude-conductor: count every open thread in my projects, rank them against my goals, and move each one to a proven finish.
```

## what you need

- Claude Code.
- a way for the agent to read your sessions: a thread or session tool in your runtime, or a browser it can use. the skill proves one real read before it relies on a route.
- your goals in order, with what "done" means for each. the run is only as good as the contract.

## files in the skill

| file | what it is |
|---|---|
| `SKILL.md` | the contract, the census, whole outcomes, authority, proof, finishing |
| `references/operations.md` | the run folder, cycles, stuck threads, sign-ins, usage limits, the review page |
| `references/launch-prompt.md` | a fill-in launch prompt |

a synthetic example lives in [`examples/claude-conductor/`](../examples/claude-conductor/sample-run.md). the test evidence is in the [evaluation](../evaluations/claude-conductor.md).

## changelog

**1.0.0** (12 Nov 2026) - first public release. this is the conductor i run on my own Claude Code threads, with my machines, accounts, thread names and private rules taken out. after a test with an agent that had never seen the skill, seven lines were made clearer: what to do with an action the contract neither allows nor forbids, how to rank threads, who arranges the independent review, what to tell a thread that waits on a protected action, how to judge a stale "running" badge, the full list of thread states, and where the cycle cursor lives.
