# Council evaluation

Version: 1.0.1

## What was tested

This release is the private skill with private paths, tools and taste files replaced by general ones. Before that, the private text reviewed itself: on 16 Nov 2026 a council ran on its own two skill files, `council` and `ship-ready`, for 5 rounds at bar 9.

Three seats, one per lab, all at high effort:

| Seat | Route |
|---|---|
| GPT-6.1 Sol | Codex |
| Muse Wonder Full | Muse |
| Claude Opus 5.5 | Cursor in rounds 1-4, after two Claude accounts hit usage limits; a Claude subscription in round 5 |

Every seat echoed the fingerprint it read, and every echo matched in rounds 3, 4 and 5. Each finding, its severity as re-rated by the author, and its outcome were kept in a ledger. The counts below come from that ledger.

## Scores

Each cell is Quality / Owner, out of 10.

| Seat | R1 | R2 | R3 | R4 | R5 |
|---|---|---|---|---|---|
| GPT-6.1 Sol | 5/7 | 7/7 | 7.5/8 | 7/7.5 | 7.5/8 CHANGES |
| Muse Wonder Full | 6.5/7 | 7.5/8 | 7.5/8 | 7.5/7.5 | 9/9 SHIP |
| Claude Opus 5.5 | 7/7.5 | 7/7.5 | 7/7 | 7.5/7.5 | 9/9 SHIP |

The lowest score rose from 5 to 7.5.

## Findings

"Raw" counts each seat's own finding. "Distinct" merges findings with the same root cause.

| Round | Raw | Distinct | Blocker | Should | Nit |
|---|---:|---:|---:|---:|---:|
| 1 | 29 | 24 | 1 | 11 | 12 |
| 2 | 19 | 16 | 0 | 9 | 7 |
| 3 | 14 | 9 | 0 | 7 | 2 |
| 4 | 10 | 7 | 0 | 3 | 4 |
| 5 | 6 | 3 | 0 | 1 | 2 |
| Total | 78 | 59 | 1 | 31 | 27 |

A merged finding takes the highest severity among its parts.

The one blocker, in round 1: ship-ready granted a push before council, so a PR with auto-merge already on could merge mid-review. Fixed by opening every PR as a draft and never changing repo settings.

Many of the mechanics in this release came from these findings: the fingerprint echo, the scope-guard formula, the rule that regressions keep their severity, the confirm round, the 60-minute seat rule with no timers, the clarifying question for nit-only CHANGES, and the git compare for a squash merge.

## Outcome

**TAP OUT at bar 9.** The lowest score was 7 in rounds 2, 3 and 4, so the no-progress rule fired after round 4. The owner chose to run round 5 anyway. In round 5 two seats said SHIP at 9/9, and Sol stayed at 7.5/8 with CHANGES.

Sol's one open should-fix was a single git command: `git show` prints a commit header, so comparing its output with `git diff` reported a difference on identical content. The fix compares the squash patch `git diff <squash-sha>^ <squash-sha>` with `git diff <base> <pr-head>`. That fix, plus a clearer 60-minute seat rule, then went to a single-seat confirm by Sol, which scored 9/9 SHIP with no new findings. Muse and Opus did not re-score that two-line change.

## Size

The two skills, with their reference files, grew from 3,399 to about 4,248 words: +25%, right at the scope guard.

## Trigger cases

[`tests/council/trigger-cases.json`](../tests/council/trigger-cases.json) holds 22 prompts that should load the skill and 22 near-misses that should not (a self-review, a proofread, a plain merge, a model question). It is a regression bank for future description changes. It has not been run as a measured trigger benchmark, so no trigger rate is claimed.

## Limits

- **A self-review, not a real task.** The council reviewed its own text. No run on a code change, a page or an email is published.
- **One run.** No spread across runs was measured.
- **The scores are model judgments.** Each one is a single sample from one model.
- **A pass was not reached.** The run tapped out at bar 9, and the final fix was confirmed by one seat only.
- **The public text was not re-reviewed.** The generic rewrite of paths, tools and roster was checked by the repository's validators, not by another council round.
- **1.0.1's full-access seat setting is wording only.** It comes from one live fleet, where seats launched on a linked machine landed supervised; no council round has run with it yet.
