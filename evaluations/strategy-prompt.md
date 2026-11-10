# Strategy Prompt evaluation

Version: 1.0.0

## What was tested

This release is the private skill with two private tool names replaced by general steps.

One forward test was run on 10 Nov 2026. A fresh Claude Sonnet session that had never seen the skill was given only the skill folder and the question in [`examples/strategy-prompt/sample-question.md`](../examples/strategy-prompt/sample-question.md). The exact Sonnet version was not recorded. The numbers below come from that one run. The math was recomputed by a script, not taken from the session's own summary.

The evidence is about whether an agent can **follow the method and keep its math straight**. It is not a measure of whether the recommendation is right. The question and every number in it are made up.

## Forward test result

| Check | Result |
|---|---|
| Output headings | All six present, in order: Options, Steelman, Scoring Algorithm, Initial Recommendation, Double-Check, Final Recommendation |
| Criteria | 6, inside the 5 to 8 range |
| Weights | Add up to exactly 100 |
| Scores | Every score is between 1 and 10 |
| Weighted totals | Recomputed from the weights and scores: A 7.40, B 7.00, C 5.25. All three match what the session stated. |
| Initial recommendation | Option A, the top of the matrix |
| Double-check | Included bias, missing criteria, a math check and "what would make me wrong" |
| Final recommendation | Option B. The double-check argued the goal criterion was under-weighted, re-ran the totals at the new weight (B 7.15, A 6.80) and showed both sets. |
| Confidence | Stated as about 55%, with assumptions and follow-up actions |
| Precision | The output says the scores are directional judgment |
| Second opinion | Recommended one from a different model before committing, and named the four scores and weights most open to dispute |

The final answer differing from the first one is the method working as written: the double-check is there to change the answer when it finds a reason.

## What changed after the test

The session reported the places where the text made it guess. Three lines were made clearer in response:

- 10 is always best for the user, so low effort and low risk score high
- the final recommendation may differ from the first, and re-scored totals are shown beside the old ones
- the note on what context was found goes at the top of the Options section

The forward test ran on the text **before** these three edits. The edited text has not been run again.

## Trigger cases

[`tests/strategy-prompt/trigger-cases.json`](../tests/strategy-prompt/trigger-cases.json) holds 22 prompts that should load the skill and 22 near-misses that should not (a quick opinion, a pros and cons list, a plan to execute, a market lookup). It is a regression bank for future description changes. It has not been run as a measured trigger benchmark, so no trigger rate is claimed.

## Limits

- **One run, one model, one made-up question.**
- **Correct math is not a correct decision.** The scores are a model's judgment. Nothing here shows that the recommended option would win in the real world.
- **The context step had nothing to read.** The test session had no notes tool, so "gather the user's own context first" was only tested as "say what you could not reach".
- **The second opinion was recommended, not run.** The skill stops at telling you to get one.
- **Weights are the agent's choice.** A different run can pick different criteria and weights and reach a different answer. The matrix makes that visible. It does not remove it.
- **No comparison against no skill.** Whether this beats a plain "which should I pick" prompt was not measured.
