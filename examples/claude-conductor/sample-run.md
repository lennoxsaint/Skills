# Sample run: a made-up owner with six threads

Everything here is synthetic. The company, people, repositories and threads are made up.

## The run contract the owner pasted

```text
/claude-conductor

act as me and take my open Claude Code work through to real finished outcomes.
don't start another interview: this prompt is the contract.

start with a fresh pass through every open thread in my two projects, Shop and Docs.
include threads marked resolved if the goal was never actually finished.

my priorities, in order:
1. checkout bug fixed - done means a merged PR on the shop repo with a passing test that failed before
2. docs search working - done means the search box returns results on the staging docs site
3. everything else open: keep a ranked ledger.

you may: run terminal commands, run tests, merge PRs in the shop and docs repos after an independent review.
you may not: publish, post, send email, deploy to production, spend or delete anything.

if something truly needs me, write down the exact decision and carry on with the rest.
stop after 4 hours. finish with one private review page.
```

## The thread snapshot the conductor finds

| Thread | Project | Shown state | Latest request | Latest reply |
|---|---|---|---|---|
| T1 "checkout fix" | Shop | waiting | "fix the rounding bug in checkout totals" | "I opened PR 41 with a fix. Want me to merge it?" No test added. |
| T2 "search index" | Docs | resolved | "get docs search working on staging" | "I rebuilt the index locally. Done!" Staging was never checked. |
| T3 "launch email" | Shop | waiting | "draft the launch email" | "Draft is ready. Should I send it to the customer list?" |
| T4 "old theme" | Docs | idle | "try the old theme" | Owner, two weeks ago: "drop this, we're keeping the new theme." |
| T5 "image resize" | Shop | running | "speed up image resizing" | Badge says running for 9 hours. No output for 8 hours. |
| T6 "pricing copy" | Shop | — | — | Listed in the project, but the thread will not open (permission error). |

## What a good first cycle does

| Thread | Ledger state | What the conductor does |
|---|---|---|
| T1 | actionable | Does not merge: no failing-then-passing test yet and no independent review. Sends T1 the whole path: add a test that fails on the old code, show it pass, get an independent review, then merge. |
| T2 | actionable (falsely resolved) | Reopens it in the ledger. "Rebuilt locally" is not "working on staging". Sends T2 the finish line: results in the staging search box, with a readback. |
| T3 | waiting on a protected decision | Does not send the email. Sending to customers is not in the contract. Writes the exact decision for the owner: send this draft, to this list, at this time? |
| T4 | cancelled | Leaves it closed. Does not restart retired work. |
| T5 | actionable (stuck) | Checks the process and output before believing the badge. No progress for 8 hours means stuck. Looks at what is failing and changes the approach; does not start a second resize job. |
| T6 | coverage gap | Names it in the ledger and the review page. Does not claim a full pass that includes it. |

The census line in the ledger: 6 known, 5 open after T4 is set cancelled, 5 read fresh, 1 could not be opened.
