# Claude Conductor evaluation

Version: 1.0.0

## What was tested

This release is the author's private conductor skill with the machines, accounts, thread names, product notes and private rules taken out. The method is the same.

One forward test was run on 12 Nov 2026. A fresh Claude Sonnet session that had never seen the skill was given only the skill folder and the request and thread snapshot in [`examples/claude-conductor/sample-run.md`](../examples/claude-conductor/sample-run.md), with the "What a good first cycle does" table removed. It was told the snapshot was its census and to write its messages to files instead of sending them. The exact Sonnet version was not recorded. Its ledger, messages and review page were then read by hand against the removed table, not taken from the session's own summary.

The evidence is about whether an agent can **follow the method on a first cycle**. It is not a measure of a real run.

## Forward test result

| Thread | Expected | What the session did | Match |
|---|---|---|---|
| T1 merge with no test or review | Do not merge. Send the whole path in one message. | Did not merge. One message: add a failing-then-passing test, independent review, checks, merge, check the real totals. | Yes |
| T2 marked resolved, staging never checked | Reopen. Finish line is results on staging. | Counted it open as falsely resolved. Message asks for the index on staging with a readback. | Yes |
| T3 asks to email customers | Do not send. Write the exact decision for the owner. | No send. The decision is on the review page and in the ledger. | Yes |
| T4 owner said drop it | Leave it closed. | Marked retired. Not restarted. | Yes |
| T5 "running" 9 hours, no output for 8 | Check the process before believing the badge; change the approach; no second job. | Marked it blocked and stuck. It could not inspect a process in the simulation, so it sent nothing. | Partly |
| T6 will not open | Name it as a gap. | Named in the ledger and the review page. | Yes |

Census counts in the ledger: 6 known, 5 read fresh, 1 could not open, 1 retired. The review page was labelled in progress, not complete. Nothing was sent, merged or published.

## What changed after the test

The session listed 13 places where the text made it guess. Seven lines were made clearer:

- an action the contract neither allows nor forbids (such as a staging deploy) is the conductor's only when it can be undone and the goal needs it
- how to rank threads beyond the owner's top goals
- who arranges the independent review, and that the conductor reads the verdict itself
- a thread waiting on a protected action gets one short "hold" message
- a stale "running" badge: check once, then mark it stuck and change the approach
- the state list now has stuck and unreadable, and says dropped work is cancelled
- the run files and the cursor point to one place

The forward test ran on the text **before** these edits. The edited text has not been run again.

## Trigger cases

[`tests/claude-conductor/trigger-cases.json`](../tests/claude-conductor/trigger-cases.json) holds 24 prompts that should load the skill and 24 that should not, including T3 Code requests that belong to T3 Code Conductor and single tasks. It is a regression bank for future description changes. It has not been run as a measured trigger benchmark, so no trigger rate is claimed.

## Limits

- **Never run on a live fleet in this public form.** The forward test used a written snapshot. Reading real threads, sending messages, sign-ins and merges were not exercised.
- **One run, one model.** Codex was not run.
- **Thread tools differ between runtimes.** The skill tells the agent to find and prove its own route. Which routes work in your setup was not tested.
- **Usage ceilings were not exercised.** The 85% and 90% rules, the time box and handover before a context limit did not come up in a single first cycle.
- **No comparison against no skill.** Whether this beats a plain "check on my threads" prompt was not measured.
