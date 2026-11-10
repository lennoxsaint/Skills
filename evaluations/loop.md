# Loop evaluation

Version: 1.0.0

## What was tested

This release is the private skill with private rubric names and product notes replaced by general ones.

One forward test was run on 10 Nov 2026. A fresh Claude Sonnet session that had never seen the skill was given only the skill folder and the request in [`examples/loop/sample-draft.md`](../examples/loop/sample-draft.md). The exact Sonnet version was not recorded. The numbers below come from that one run. They were then checked by a script and by reading the output, not taken from the session's own summary.

The evidence is about whether an agent can **follow the contract**. It is not a measure of how good the final email is.

## Forward test result

| Check | Result |
|---|---|
| Rubric | 6 criteria. Weights 25, 20, 20, 15, 10, 10. They add up to 100. |
| Hard veto | One criterion was marked as a hard veto (use only the four listed facts). |
| Starting score | 26 of 100, with each lost point named |
| Loop 1 | 97 of 100. The per-criterion scores add up to 97. |
| Loop 2 | 100 of 100. The per-criterion scores add up to 100. |
| Status | `score_100` after 2 loops |
| Facts | The final email uses the four listed facts and keeps the qualifiers on the speed claim ("5,000-note library", "in our own test"). Nothing else is claimed. |
| Source file | Byte-identical to the original after the run |
| Live actions | None. The scorecard says nothing was sent, scheduled or published. |
| Self-scoring | The scorecard says the session scored its own drafts and points to Hill Climb for a measured bar. |

## What changed after the test

The session reported the places where the text made it guess. Three lines were made clearer in response:

- what a hard veto does to the status
- that the adapter file is in the skill's own folder
- that the scorecard must say the loop is self-scored

The forward test ran on the text **before** these three edits. The edited text has not been run again.

## Trigger cases

[`tests/loop/trigger-cases.json`](../tests/loop/trigger-cases.json) holds 22 prompts that should load the skill and 22 near-misses that should not (a hill climb, a one-line fix, a prompt to run later, a plain review). It is a regression bank for future description changes. It has not been run as a measured trigger benchmark, so no trigger rate is claimed.

## Limits

- **One run, one model, one kind of draft.** A short email is the easy case. Thumbnails, video and carousels use adapters that were not forward-tested in this public copy.
- **A 100 here is a self-score.** The agent that wrote the draft also graded it. The result proves the scorecard is consistent, not that a reader would prefer the email.
- **`blocked_below_100` was not seen.** The run reached 100, so the stop-below-100 path, the 10-loop cap and the two-loops-with-no-gain rule were not exercised.
- **The refusal paths were not triggered.** The request said "do not send anything", and the session obeyed. A request that tries to push a live action was not tested.
- **No comparison against no skill.** Whether the loop beats a plain "improve this" prompt was not measured.
