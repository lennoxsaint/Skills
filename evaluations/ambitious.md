# Ambitious evaluation

Version: 1.0.0

## What was tested

This release is the private v1.2.3 body plus the 28 Oct 2026 trigger fix. The quality benchmark below ran on the v1.2.3 body (the same file, checked by hash). The trigger fix changes only the `description` that decides when the skill loads, so it was tested separately.

## Quality benchmark: with the skill vs without

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

A later private version (v1.3.0) was benchmarked against v1.2.3 under a rule set before the run. It fell short of that rule on one task, so v1.2.3 was kept. That is the body published here.

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

- Three tasks and three runs per arm is a small sample. The run-to-run spread is wide enough that one task could flip with more runs.
- The judge is a model. A blind judge can still have taste that differs from yours, so the flight report shows the evidence and not just the score.
- The trigger numbers come from one private setup (Claude Opus 5.5, 26 probes run three times each). Other hosts, models and personal rule files may route skills differently.
- The skill grants no authority. Results that need a send, a publish or a deploy stop at a prepared move and wait for a yes.
