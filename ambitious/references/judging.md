# The outside judge

Felix, October 2026: "Do not ask the model to judge itself... insist on outside validation. Ideally that's a tool the model can run to get feedback immediately." This file explains how to do that.

## Order of judges
1. **A tool that measures.** Tests, `ffprobe`, a loudness meter, Lighthouse, axe, a schema validator, a query re-run that reproduces a number, a rendered screenshot. Tools are fast, cheap and can't be flattered. Run them first and fix what they find.
2. **A different model.** `scripts/judge.mjs` sends the work to Codex (`codex exec`, read-only sandbox, no user config, nothing persisted). A different model family has different blind spots from yours.
3. **A fresh instance.** If Codex isn't installed, is stopped, or replies without a valid verdict, `judge.mjs --judge auto` falls back to a fresh Claude process with no conversation history and read-only file access. Where the CLI supports `--safe-mode` it runs with it, so the person's CLAUDE.md, skills, hooks, plugins and MCP servers stay off and the judge sees only the brief and the work; the verdict's `label` says which happened. Every attempt is listed in `attempts`.

Independence is measured, not assumed. `judge.mjs` compares the judge's model family with yours (`author_model` from `flight_check.mjs init --author-model`, or `--author-model`), and reports `different_family`, `same_family_fresh_context` or `unknown`. Report it as given. A same-family judge still beats self-grading, but it shares more of your blind spots.

**Fails closed.** A reply counts as a verdict only if every dimension has a number from 1 to 10 and a line of evidence, plus a top fault and a fix. Anything else is `invalid`: report it as no verdict. A judge that exits cleanly with no readable verdict gets one retry. Every failed attempt keeps its full reply (secrets redacted) in the verdict file, so the failure can be diagnosed. Each verdict file is new (`judge-<round>-<kind>.json`, then `-2`, `-3`) and carries an `artifact_digest` of exactly what was judged.

If none of these can run, record `"judge: none available – <reason>"` in `gaps`. Never fill the hole with your own score.

## What the judge sees
- **The brief:** what was asked, who it's for, the money moment, the bar. Write it as the person and the audience would state it.
- **The artifact:** the deliverable itself as the person will receive it.
- **The evidence:** tool reports, screenshots, contact sheets, the fact sheet.
- **Not** your verdict, your reasoning, your flight log or your opinion of how it went. A judge that knows what you think anchors on it.

`judge.mjs` copies the artifacts into a neutral scratch folder and redacts secret-looking strings (API keys, tokens, private keys) before the judge sees anything. Per-person privacy rules live in the profile.

## Preparing each medium
`judge.mjs` does most of this automatically:
| Medium | What the judge gets |
|---|---|
| Video (.mp4, .mov, .webm, .m4v) | `ffprobe` summary (duration, resolution, fps, audio, loudness if measured), a contact sheet of ~24 evenly spaced frames, a **hook sheet** (first 3 s) and a **CTA sheet** (last 6 s), and a whisper transcript with timestamps (`--transcribe`, on by default for video). |
| Web page (.html) | Rendered screenshots at 390 px (mobile) and 1440 px (desktop) via headless Chrome, plus the HTML source. |
| Images | The images themselves. |
| Text, markdown, data, code | The files, read directly by the judge in its sandbox. |
| A folder | Everything inside, with the rules above applied per file. |

Stills and a transcript can't show a video's pacing, its sound or how a cut feels. Measure those with tools (cut timing, loudness, silence gaps), pass the numbers in as evidence, and tell the person what the judge couldn't see.

If a medium needs something the script doesn't do (say, a live app that has to be clicked through), capture it yourself: screenshots, a GIF, a recording or a log. Then pass those in as artifacts.

## The rubric
Each dimension is scored 1–10, and each score comes with one line of evidence.
| Dimension | The question |
|---|---|
| **fit** | Does it do exactly what was asked, for the person and audience in the brief? |
| **depth** | Is the top professional's method visible, built from raw material with real instruments? Is it correct? |
| **craft** | No rough edges, intentional choices, a bespoke rather than generic feel? Does it follow the fundamentals of its medium? |
| **money_moment** | How well does it drive the decision it exists to cause (the CTA, the buy, the yes)? |
| **truth** | Is every claim sourced or verifiable, with nothing invented and unknowns labelled? |
| **delight** | Is there something unasked-for that is obviously right and that the person would keep? |

The judge also names the **top fault** (the single change that would most improve the work) and the **would-keep list** (the unasked-for things a reader would keep).

**Default bar:** every dimension ≥ 8 and truth ≥ 9. A truth failure is a fail regardless of the other scores. Raise the bar with `--bar` for Max runs or for reusable work.

## The loop
Before an expensive build, `--concept` judges the plan, script or storyboard as round 0. It is logged but never counts as the verdict on the finished work.

```
round 1: judge → fix the top fault (and anything truth-related) → round 2: judge → ...
```
- Fix the **top fault** first. It's usually worth more than everything else on the list combined.
- Re-run the tool checks after every fix, because fixes break things.
- Stop when the bar is met or the tier's rounds are used up (Lean 1, Standard 3, Max 5). If the bar isn't met, report the last verdict as it stands and own it in `gaps` as `"bar: ..."`. That's an honest result, not a failure of the skill. `flight_check` refuses a final fail that isn't owned.
- For Max: build two variants and run `judge.mjs compare`. It runs both blind orders itself and names a winner only when they agree. A judge that picks whichever entry it saw first (or second) both times is showing position bias, and the result says `no_consistent_winner`. Then two different judges (`--judge codex` and `--judge claude`, or Codex with a different `--model`) score the final version. Both must pass with the same `artifact_digest`. `flight_check` checks this.

## Commands
```bash
# score one deliverable (writes <run>/judge-<round>-<kind>.json and appends it to flight.json; round defaults to the next one)
node scripts/judge.mjs score --run <run-dir> --brief <brief.md> --artifact <path> [--artifact <path> ...] \
  [--round N | --concept] [--bar "all>=8,truth>=9"] [--judge auto|codex|claude] [--author-model <id>] [--timeout-sec 900] [--no-transcribe]

# blind A/B: neither label nor path tells the judge which is which. Runs both orders and reports winner_input
# (a, b, tie or no_consistent_winner) plus position_bias. --swap or --one-order runs a single order.
node scripts/judge.mjs compare --brief <brief.md> --a <path>... --b <path>... --out <verdict.json>
```
Read the JSON it prints: `verdict`, `scores`, `top_fault`, `fix`, `would_keep`, `independence`. In our own tests one blind pairwise order picked the second-shown entry both times, so pair a compare with an absolute `score` of each candidate when the call matters. If `status` isn't `ok` (`stopped`, `no_verdict`, `invalid`, `unavailable`), there is no verdict. Say so, and don't guess what it would have said.

## Writing the brief file
```markdown
# Brief
Ask (verbatim): <the person's words>
Deliverable: <what exactly is being judged>
Audience: <who will see it, and in what situation (scrolling a phone, deciding to buy...)>
Money moment: <the decision it exists to cause>
Stretch targets: <the measurable ones, with how they were measured>
Constraints: <brand rules, length, platform, facts that must hold>
Run limits: <what this run could not do, e.g. nothing sent, no live checkout, no production writes. Put these in from round 1 so the judge scores the work against what was possible; changing the brief mid-loop resets the comparison>
Facts the judge can check against: <path to fact sheet or source data, if any>
```
