# Adversarial Review evaluation

Version: 1.0.0

## What was tested

This release is the private skill with notes about private machines replaced by general ones. One product-specific reference file was left out.

One forward test was run on 10 Nov 2026. A fresh Claude Sonnet session that had never seen the skill was given only the skill folder and the plan in [`examples/adversarial-review/sample-plan.md`](../examples/adversarial-review/sample-plan.md). It was told not to read the list of planted faults at the bottom of that file. The exact Sonnet version was not recorded. The test budget was two scored rounds, one fewer than the skill's default of three.

The reviewer was GPT-6.1 Sol through the Codex CLI (0.167.0-alpha.3.2), in a fresh read-only session with no tools. The model name was read from the CLI's own run header.

The numbers below come from that one run. The hashes and sums were recomputed by a script, not taken from the session's own summary.

The evidence is about whether an agent can **run the review honestly**. It is not a measure of how good the reviewed plan became.

## Forward test result

| Check | Result |
|---|---|
| Rubric | 5 categories written before round 1 (30, 20, 20, 15, 15). They add up to 100 and stayed the same in round 2. |
| Snapshots | Two numbered versions of the plan. Each manifest hash and digest recomputes to the stored value. |
| Reviewer label | `different_family`, with the actual model recorded in each receipt |
| Reviewer input | The prompts and snapshots contain no text from the answer sheet |
| Round 1 | 9 of 100, not accepted. 7 findings: 3 critical, 2 high, 2 medium. |
| Planted faults | All 3 were found in round 1: reads switched before the copy, the old database deleted with no check or way back, and a success test that can't be measured. |
| Extra findings | 4 more that were not planted (writes during the copy, an unspecified export script, no owners or dates, late customer notice) |
| Round 2 | 52 of 100 on the revised plan, not accepted. 6 findings: 1 critical, 3 high, 2 medium. |
| Receipt math | In both rounds the category scores add up to the stated total |
| Stop | The 90 bar was not met inside the two-round budget. The report says "bar NOT met", lists the open critical and high findings and claims no pass. |
| Scope | Review only. The report says the plan was not carried out. |

The run ending below the bar is a useful result. The skill's job at that point is to stop, keep the best draft and say so, and it did.

## What changed after the test

The session reported the places where the text made it guess. Three lines were made clearer in response:

- when the user gives no rubric, write one from the brief before round 1 and keep it fixed
- the real model name may come from the tool's run header as well as its usage metadata
- record `default` as the requested model when none was named

The forward test ran on the text **before** these three edits. The edited text has not been run again.

Two more notes from the session were left alone, because the fix belongs to the reader's own tools: the skill does not map "fresh session, no tools" to one CLI's flags, and it says to read the tool's current help each time for that reason.

## Trigger cases

[`tests/adversarial-review/trigger-cases.json`](../tests/adversarial-review/trigger-cases.json) holds 22 prompts that should load the skill and 22 near-misses that should not (a plain code review, a proofread, a self-check, a request to build the thing). It is a regression bank for future description changes. It has not been run as a measured trigger benchmark, so no trigger rate is claimed.

## Limits

- **One run, one reviewer, one made-up plan.**
- **A pass was never seen.** The run stopped at 52 of 100. The path where the bar is met and the findings are closed was not exercised.
- **The agreement path is untested.** No run asked the author and the reviewer to endorse the same frozen version.
- **Only the Codex CLI reviewer was used.** A Claude CLI reviewer and a same-family fresh session were not exercised in this public copy. In the test session the Claude CLI help command hung, so that route was skipped.
- **One sample per round.** The jump from 9 to 52 is two single reviews. Reviewer scores vary from run to run, and no spread was measured.
- **The model check used the run header.** The CLI's JSON output carried no model name in this version.
- **A review score is not product proof.** A reviewed plan is still a plan nobody has run.
