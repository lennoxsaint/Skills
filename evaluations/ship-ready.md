# Ship-ready evaluation

Version: 1.0.0

## What was tested

Ship-ready has never run end to end on a real task. Its text was reviewed: it was one of the two files in the five-round council described in the [Council evaluation](council.md), so three seats from three labs scored it and their findings were fixed. The round-1 blocker, a push granted before council so a PR with auto-merge on could merge mid-review, was in this skill.

Findings from that review that changed this skill:

- every PR opens as a draft, and repo settings are never changed
- before the first push, check whether the push alone could trigger the go
- re-check auto-merge and the merge queue before marking a PR ready
- a two-lab result is NOT READY unless the user waived the third lab
- a SINGLE-SEAT PASS is READY only when the user asked for one reviewer
- what is staged is compared with the version council passed, with a confirm round if it differs
- for a squash merge, compare `git diff <squash-sha>^ <squash-sha>` with `git diff <base> <pr-head>`
- push and PR rights come only from the words "ship-ready" or "full stop"

## Acceptance cases

Expected results only. None of these has been run.

| Case | Expected result |
|---|---|
| "ship-ready" on a bug fix in the user's repo | Commits to a task branch, opens a draft PR, gets CI green, runs council, marks the PR ready, stops before merge |
| Skill loaded by other wording | Works locally and asks once before the first push or PR |
| Push would deploy (deploy-on-push branch) | Stops with BLOCKED before pushing; repo settings unchanged |
| Auto-merge turned on after the first push | Re-checks before marking ready; reports BLOCKED instead of marking it ready |
| Council passes with only two labs, no waiver | Hands back NOT READY |
| Council taps out | Hands back NOT READY with the best version, each open dispute and one unblocking step |
| Staged email differs from the version council passed | Runs a confirm round; NOT READY unless it passes; sends nothing |
| Pre-authorized squash merge to staging | Compares the squash patch with the reviewed diff, confirms if they differ, retests, then sends the one release message |
| User needs to supply a secret | Asks only for that, and settles reversible choices itself with each one logged |
| Ready | One READY message with the go action, council scores, proof paths and choices made; then waits |

## Trigger cases

[`tests/ship-ready/trigger-cases.json`](../tests/ship-ready/trigger-cases.json) holds 22 prompts that should load the skill and 22 near-misses that should not (a direct merge, a send, a rough draft, a plain PR review). It has not been run as a measured trigger benchmark, so no trigger rate is claimed.

## Limits

- **Never run end to end on a real task.** No READY or NOT READY hand-back has been observed.
- **The review was of the text.** Model scores on its wording say nothing about whether staging works on a real repo or mail app.
- **It depends on Council**, whose own evidence is one self-review run that tapped out at bar 9.
