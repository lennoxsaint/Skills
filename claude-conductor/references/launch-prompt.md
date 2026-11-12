# Launch prompt

A template the owner fills in and pastes into a fresh Claude Code session to start a run. Replace every `<...>`. Delete lines that do not apply.

Keep it in plain words. The conductor treats this prompt as the whole run contract and will not interview you again.

```text
/claude-conductor

act as me and take my open Claude Code work through to real finished outcomes.
stay on <model> in this session. don't start another interview: this prompt is the contract.

start with a fresh pass through every open thread in <projects or "all my projects">.
read each thread's latest request and reply. include threads marked resolved if the goal
was never actually finished. keep cancelled and retired work as it is.

my priorities, in order:
1. <outcome> - done means <evidence you will accept>
2. <outcome> - done means <evidence>
3. everything else open: keep a ranked ledger so nothing drops off.

use the thread that already owns each piece of work. give it the whole outcome:
reproduce, fix, show it failing then passing, review, the checks this project needs,
the merge this project allows, then the real result. not one step per message.
you may create a new thread only for a gap with no owner.

you may: <run terminal commands, run tests, merge PRs in <repos> after review, sign in with my saved logins, ...>
you may not: publish, post, send to real people, schedule, spend or delete anything,
unless it is listed here: <exact approved actions, or "nothing">.

if a thread was nudged twice with no progress, look at what is actually failing and change the approach.
if something truly needs me, write down the exact decision, keep it in the ledger and carry on with the rest.

check the usage meter before big dispatches. wind down at 85%, stop new dispatch at 90%.
if you can't read it, stop after <hours> hours. a reset does not extend the run.

report outcomes with proof, not prompts sent. finish with one private review page:
each goal, what's actually done, the proof, every thread's final state, and what still needs me.
```

## Notes on filling it in

- **Priorities.** Give each one a finish line you could check yourself: a file, a merged PR, a passing test, a provider readback. "Make progress on X" gives the conductor nothing to stop on.
- **Authority.** Name repositories, accounts and exact actions. The conductor reads anything unlisted as not allowed.
- **Time box.** Pick one even if you can read usage. It is the fallback when the meter is unreadable.
