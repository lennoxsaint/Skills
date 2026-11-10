---
name: hill-climb
description: Turn real data into a locked answer key, then climb toward a measured target with fresh agent sessions until the number and two outside judges say it is done. Use for long, ambitious work that must reach a provable quality bar - "hill climb this", "build an eval and climb it", "make the harness/app/agent hit X%", "use the logs as a benchmark", "keep going until it passes", or any big job where vibes are not enough. For quick polish of one draft use `loop` instead.
---

# Hill climb

A **hill** is one goal with a locked **answer key** (yes/no test cases built from real data) and a runner that **climbs** it: baseline, one change, score, keep or undo, repeat, all on disk. The verifier sets the ceiling, so most of the craft is the answer key; the climb itself is a script.

Two stages decide **done**:
1. **Tests**: the visible-test score reaches the target, the hidden tests stay within 5 points, and no must-pass case fails. When the hidden check is what blocks, a change that holds the visible score and raises the hidden score is kept.
2. **Council**: two judges from different labs (GPT-6.1 Sol and a fresh Opus by default) score the result per rubric category, 1-10 in half points, and say whether they would ship it; the climb continues on their critiques until every judge gives the bar (default 9) in every category and would ship. The judges are blind: they never see the target, the bar or the test score. For visual work they score rendered screens next to frozen **references** (the best products you know) and the starting version, shuffled under letters, and the work must lead every reference. Each judge scores those screens in a look call that sees nothing else, then gives its ship vote in a separate review call with the code and diff. A stage-2 change is kept only when nothing slips (the lowest, the total, any ship vote) and something rises; a judge whose score rose is asked a second time before it counts.

Scripts live in `scripts/` next to this file (call it `$HC`). Every command prints JSON. State lives in the **hill folder** (default `~/.hill-climb/hills/<name>`); the climber edits a separate **work folder** on its own `hill/<name>` git branch.

## Steps

### 1. Frame the hill
Write down, in one sentence each: the goal, the files the climber may change (**climbable**), what the score measures, and a stretch target number. Then create the hill:

```bash
node $HC/hill.mjs init ~/.hill-climb/hills/<name> --name <name> --repo <git repo> [--base <ref>]   # or --scratch
```

Fill `hill.json` (every field: [references/hill-json.md](references/hill-json.md)). Read [references/safety.md](references/safety.md) when the work folder is a real product repo.
For the council, draft a `council_rubric` of 3-6 categories from the owner's own critiques (for UI: typography, hierarchy, colour and contrast, consistency, iconography), and for anything visual a `council_render` command that screenshots the work (headless, never the owner's screen).
**Done when** `goal`, `climbable`, `metric.name` and `metric.target` hold real values and no `TODO` remains.

### 2. Mine the raw data
Go to the data that already exists: logs, transcripts, tool-call history, past outputs, owner corrections, support tickets, analytics, the owner's own edits to drafts. Recipes per domain and the transcript miner (`scripts/mine_tools.mjs`) are in [references/answer-key.md](references/answer-key.md).
**Done when** you hold at least 20 real examples, each with its source path or URL, and you can say in one line what "good" and "bad" look like in this data.

### 3. Pick exemplars
Choose 3-10 real outputs that the data (or the owner) already marks **good** or **bad**: a post the owner rewrote, a tool call that failed, a reply that won. Save each to `exemplars/<id>.json` with its `input`, the real `output`, its `label` (`pass`/`fail`) and the checks that should tell them apart.
**Done when** at least 3 exemplars exist and both labels are present.

### 4. Write the answer key
Turn what separates good from bad into **yes/no checks**: code checks first (exact values, regex, length, a command), then binary LLM `judge` checks for what code cannot see. Never use 1-10 scales inside a case. Check types and the case format: [references/answer-key.md](references/answer-key.md).
**Done when** every exemplar's checks pass the good ones and fail the bad ones when run (step 6 measures this).

### 5. Grow the cases
Turn each real example into a case in `cases/pool/`, then synthesise more around the edges the real ones reveal until there are about 50 or more. Mark each case `origin: real|synthetic`; add **negative** cases (the right move is to do nothing or refuse) and mark the few cases that must never fail as `must_pass`. Write `scorer/produce.mjs`: given `{id, input}` on stdin it runs the current work folder offline and prints the output under test (env, sandbox and a worked recipe: [references/answer-key.md](references/answer-key.md#the-producer)).
For a render hill, put 1-3 references in `references/<id>/` (screenshots of the best products you know, plus `manifest.json`) and run `node $HC/hill.mjs council-test <hill>` once: it asks the judges about the current commit and records nothing, so you can see the rubric and references work before freezing.
Score the pool twice before splitting (`node $HC/hill.mjs score <hill> --split pool`). The gap between the two runs is the noise: set `accept_margin` above it, or turn on `confirm_gains` or `repeats`, and set the target and a stretch number from the baseline.
**Done when** the pool has 30+ cases including real, negative and must-pass ones, `node $HC/hill.mjs try <hill> --case <id>` runs one case end to end inside the sandbox, and you know the baseline and its noise.

### 6. Split, validate, freeze
```bash
node $HC/hill.mjs split <hill>            # ~30% hidden, stratified; --reset to redo it
node $HC/hill.mjs validate <hill> --run   # structure + exemplar discrimination
node $HC/hill.mjs freeze <hill>           # locks the key with hashes
```
Fix every problem `validate` reports and rerun it. Discrimination below 0.8 means the answer key cannot yet tell good from bad: fix the checks, never the exemplar labels (`validate --run` lists each misclassified exemplar's failed checks; `judge-test` tries a judge question alone).
**Done when** `freeze` prints `status: ok`.

### 7. The owner checkpoint
Commit the starting files on the hill branch first: the baseline needs a clean folder.
```bash
node $HC/hill.mjs brief <hill>   # measures the baseline, writes checkpoint.html
```
Show `checkpoint.html` to the owner (in Claude Code, publish it as a private Artifact; elsewhere, send the file). It is the one-page answer key: goal, today's score, target, sample tests, how done is decided (with the rubric, the references and today's render), stop rules and scope. This is the only stop for the owner; after it the climb is hands-off. When they say go:

```bash
node $HC/hill.mjs approve <hill> --by <owner name>
```
**Done when** `approve` prints `status: ok`. Changing the key after this means `freeze` again and a new approval.

### 8. Climb
Start the runner as one long background process and let it run; it wakes nobody until it stops.

```bash
node $HC/climb.mjs <hill> [--deadline 2026-11-03T09:00:00+08:00] [--max-attempts N]
```

Each attempt is a fresh agent session (`claude -p` or `codex exec`) that sees the goal, the score, failing visible tests, its own past attempts and `notes.md`, makes ONE change, and stops. The runner scores it, keeps it as a commit or saves it as a `refs/hill/<name>/rejected/<n>` ref and puts the folder back, and writes `state.json`, a hash-chained `ledger.jsonl` and `board.html` (the live scoreboard). Producers, checks, judges and climbers (Claude or Codex) run sandboxed away from the hill folder, with writes denied outside their own folders ([references/safety.md](references/safety.md)). Each outcome is written to `runs/<n>/decision.json` before git is touched, so a killed run resumes with the same command, records every outcome exactly once and loses nothing.

It prints one JSON line and exits with a **status**:

| status | exit | meaning and next move |
| --- | --- | --- |
| `done` | 0 | stage 1 and the council passed: land it |
| `stuck`, `deadline`, `max_attempts`, `budget`, `stopped` | 0 | report the best and propose the next move; `deadline` also covers scoring or a council review cut off by the deadline; `budget` means `stop.budget_usd` was spent (runs of unknown cost are not counted); `stopped` also covers `--once`, `--recover-only` and a signal (exit 130) |
| `stage1_only` | 0 | stage 1 met under `--no-council`: NOT done; run again without the flag for the judges |
| `saturated` | 0 | every visible test passes but the hidden score lags: add cases that cover the hidden failures, re-freeze |
| `blocked` | 2 | needs the owner: wrong branch, foreign changes, git files changed (`--accept-git-config`), touched ignored files, not approved |
| `tampered` | 2 | the answer key changed during an attempt: find out why before anything else |
| `busy` | 3 | another runner holds this hill |
| `error` | 1 | climber, judge or scorer failing three times in a row, or a crash: read `stop_reason` and `runs/<n>/` |
In stage 2 the judges run in `council` list order (cheapest first): after a full-panel first round, a later judge is asked only when the earlier ones pass. The board shows before, after and the references side by side, every round's category scores and leads, drift flags, and the spend. While it runs, republish `board.html` at milestones (first keep, stage 2 reached, stop). Add a learning to `notes.md` when you spot one; the next attempt reads it (the judges never do).
**Done when** the runner exits and `report.md` exists.

### 9. Land it
Read `report.md` and the stop reason, and run `node $HC/hill.mjs verify <hill>` (ledger chain and lock intact). On **done**, the `hill/<name>` branch holds the result: open a PR or hand it over within the authority in `hill.json`. On **stuck** or **deadline**, report the best score, the top failing tests and the judges' last critiques, and propose the next move (better answer key, a bigger change, more time).
To go further after **done**, raise the bar: `node $HC/hill.mjs raise <hill> --bar 9.5 [--focus "what the owner cares about now"]` saves the result as branch `hill/<name>-level-9`, re-freezes with the new bar, and needs `brief` + `approve` again. Steer taste here, through the bar and the focus line, never by editing the judges' inputs.
**Done when** the owner has the final board, the numbers (baseline -> best -> target, hidden score, judge scores) and the PR or next move.

## Commands
`hill.mjs status|score|try|discriminate|judge-test|council-test|raise|verify|board <hill>`: read the current state (including earlier `generations` and the spend), rescore a split (`--split optimise|holdout|both`), run one case end to end (`--case <id>`), recheck the exemplars, try one judge question, ask the council once about a commit without recording it (`--sha <ref>`), raise the bar after done, verify the chain and lock, rebuild the board. `climb.mjs <hill> --recover-only` cleans up after a killed run without climbing; `--once` runs one attempt; `--no-council` climbs stage 1 only and stops as `stage1_only`. `node $HC/selftest.mjs [--only A,B]` proves the runner mechanics with scripted fake agents (no model calls).

## Limits
- The hidden tests sit on the same disk. The sandbox hides the hill folder from every climber, producer, check and judge; prompts never show them; diffs that paste test text are rejected; the key is hashed; and a hidden score more than 5 points behind the visible one blocks stage 1. With `"sandbox": "off"` none of that hiding applies. Other limits: [references/safety.md](references/safety.md#known-limits).
- A score is only as good as its answer key. When the climb reaches the target but the owner still dislikes the result, the fix is new cases from that dislike and a new `freeze`, not more climbing.
