# Ambitious evaluation

Version: 1.3.1

## What was tested

This release is the private v1.3.1 skill: the v1.3.0 body plus the 28 Oct 2026 trigger fix. It is the version the author runs every day. The body is leaner than v1.2.3: extra crew fields, the working sketch, the review page and the taste log now run only when they fix a problem you can name for the real audience.

Read the two benchmarks below together:

- **With the skill vs without** ran on the **v1.2.3** body, the one published before this release. The v1.3 body has not been run against "no skill".
- **v1.3.0 vs v1.2.3** ran head to head. The v1.3 body came out about even, a little cheaper, and it **missed the adoption rule that was set before that test**. The author chose to publish it anyway on 10 Nov 2026. The reasons and the numbers are under "Version choice".

The trigger fix changes only the `description` that decides when the skill loads, so it was tested separately.

## Quality benchmark: with the skill vs without (v1.2.3 body)

Three tasks, each run three times with the skill and three times without it. The same executor model ran both arms. A different model judged every output blind: it saw the brief and the work, never which arm made it. Each output got six scores from 1 to 10 (fit, depth, craft, money moment, truth, delight). The table shows the mean.

| Task | With the skill | Without | Call |
|---|---:|---:|---|
| Revenue-leak analysis | 7.22 | 6.11 | better |
| Coach landing page | 7.89 | 6.44 | better |
| Reel edit | 6.06 | 5.44 | tie |
| **All three** | **7.06** | **6.00** | about 17% higher |

The rule for calling a task a win, a lean win or a tie was written down before the results were read. The reel edit is reported as a tie because its runs did not agree.

**Cost.** With the skill, a run took about 1.3-2x the time and tool calls of a run without it.

## Version choice

On 27 Oct 2026 the v1.3.0 body was benchmarked against the v1.2.3 body: the same three tasks, three runs per version, the same executor model, and a different model judging blind. Each pair of outputs was compared in both orders and each output also got its own score (the mean of six 1 to 10 scores).

| Task | v1.3.0 | v1.2.3 | Difference | Call for v1.3.0 |
|---|---:|---:|---:|---|
| Revenue-leak analysis | 6.50 | 6.61 | -0.11 | tie |
| Coach landing page | 7.28 | 7.61 | -0.33 | tie |
| Reel edit | 5.94 | 5.44 | +0.50 | win |

Per run, v1.3.0 was about 12% faster, used 11% fewer tool calls and 12% fewer transcript tokens.

**The rule, written before any run:** keep v1.3.0 only if it loses no task and its mean score is not more than 0.3 below v1.2.3 on any task. Otherwise go back to v1.2.3.

**The result by that rule:** go back to v1.2.3. v1.3.0 lost no task, but on the coach landing page it was 0.33 below, against a limit of 0.30. That is a narrow miss and it sits inside the run-to-run spread (standard deviations of 0.54 and 0.70 on that task). The rule is mechanical, so the miss stands as a miss.

**What was published, and why:** the first public release (v1.2.4) followed the rule and shipped the v1.2.3 body. This release ships the v1.3 body. That is the owner's decision on 10 Nov 2026, not a new test result: it is the version he has run every day since 28 Oct 2026, it costs less per run, and this repository is meant to hold the skills he uses. No new benchmark was run for this release. If you want the body that passed the rule, install the `ambitious-v1.2.4` release.

## Trigger accuracy

The 28 Oct trigger fix narrowed when the skill fires. "Before" is the v1.2.3 description; "after" is the fixed one shipped here.

- Asks that should fire the skill fired it in 12 of 12 runs.
- Near-miss asks that should not fire it (for example a plain "write a sales page" or "create a skill") dropped from 67% false fires (44 of 66 runs) to 18% (12 of 66).

The public trigger bank in [`tests/ambitious/trigger-cases.json`](../tests/ambitious/trigger-cases.json) holds 24 positive and 24 near-miss negative prompts written for this repository. It is a regression bank for future description changes, not the private set behind the numbers above.

## Script checks

`node ambitious/scripts/selftest.mjs` runs 58 checks and all 58 pass. It uses fake judges to prove that:

- the judge only counts a reply when every dimension has a score and a line of evidence;
- the judge falls back from Codex to a fresh Claude process and reports every attempt;
- the judge reports whether it is the same model family as the author, instead of assuming it is independent;
- verdict files are never overwritten;
- the flight check fails a run whose only judge saw the concept and not the work, a missed target or a failed verdict that isn't owned as a labelled gap;
- a Max run needs two different judges to pass the same final version;
- editing the work after a verdict makes that verdict stale.

CI runs the self test on every push.

## Limits

- **The shipped body missed its own adoption rule by 0.03 on one task** and has no "with vs without" benchmark of its own. The 17% figure above belongs to the v1.2.3 body.
- Three tasks and three runs per arm is a small sample. The run-to-run spread is wide enough that one task could flip with more runs.
- The judge is a model. A blind judge can still have taste that differs from yours, so the flight report shows the evidence and not just the score.
- The trigger numbers come from one private setup (Claude Opus 5.5, 26 probes run three times each). Other hosts, models and personal rule files may route skills differently.
- The skill grants no authority. Results that need a send, a publish or a deploy stop at a prepared move and wait for a yes.
