---
name: council
description: Council review loop. Reviewers from three different AI labs score the work, the author fixes what they prove, and the loop repeats until every reviewer clears the bar. Use when the user says "council" or "council 9.5", model council, multi-model or cross-lab review, red-team or adversarial review across labs, "get the models to agree", or wants output ready to send, ship or publish without reading it themselves. Also the review gate inside ship-ready. For one reviewer against a 100-point rubric, use adversarial-review.
---

# Council

Work goes out only when three outside minds would ship it. Each **round**, one seat from each of three labs scores one exact version, its **fingerprint**. You check every finding against its **proof**, fix the ones that hold up with the smallest change, and send the new version back. The loop ends at the **bar**, at a **tap out**, or on a blocker. Then the user gets a one-screen **receipt**, and you stop before anything goes out.

Different labs catch different things. Two models from the same family review like one person at two times of day. In Theo Browne's council video (2026-11-16), runs climbed from about 7.5 to 9 out of 10 in two or three rounds. The same runs show the failure this skill guards against: with no cap, one loop ran 50+ rounds and grew a 1k-line change past 20k lines.

## Read the call

| The user says | Bar | Mode |
|---|---|---|
| `council`, `model council`, a red-team or adversarial review across labs | 9 | Review: three labs |
| `council 9.5` | 9.5 | Review: three labs |
| `council: would <person> be happy with this` | 9 | Review, with that question as the second axis |
| one reviewer named, for example "council with GPT only" | 9 | Single seat: the same loop with that reviewer |
| a decision or strategy question with no artifact yet | n/a | Decide: [references/decide.md](references/decide.md) |

Every seat gives two scores out of 10:

- **Quality**: is it correct and complete for its audience?
- **Owner**: would the user ship it exactly as it is? Seats judge this from the taste and brand files the user names, plus `$COUNCIL_TASTE_FILE` when it is set. With no such file, they judge it from the intent and audience in the brief, and the brief says so.

A **pass** needs all of these, on the same fingerprint:

- three labs seated, unless the user waives the missing ones for this run
- every seat at or above the bar on both axes, with `VERDICT: SHIP`
- no open blocker or should-fix, including any concern of your own

A missing score counts as below the bar. Asking for one reviewer waives the other labs, and its pass is reported as SINGLE-SEAT PASS, never as a council pass.

## 1. Prepare

1. Finish the work before round 1. Fix known issues, run the checks, and render what people will see. The council reviews your best version.
2. Freeze the **brief** from [references/brief.md](references/brief.md): the intent, what is out of scope, the audience and the consequence, the checks you ran and their results, the artifact, and the paths to the taste and brand files. Keep the bar out of the brief so it doesn't anchor the scores.
3. Take the **fingerprint**:
   - In git, commit the work to the task branch. The commit SHA is the fingerprint.
   - Otherwise, take the SHA256 of each artifact file.
4. Record the **base** and the **baseline**, once, and keep both fixed for the run:
   - Base (code): `git merge-base <target branch> <sha>`, the commit the work started from.
   - Baseline: the round-1 size. Code: insertions plus deletions from `git diff --shortstat <base> <sha>`; new files count, since they are committed. Prose: the word count.
5. Keep the ledger and receipt outside the artifact paths. Never commit them, and leave them out of the fingerprint and the size.

Done when the brief would let a stranger review the work with no chat history.

## 2. Seat the council

Resolve the seats from what is live on this machine. In T3 Code, call `orchestrator_capabilities` once.

| Seat | Ladder: first rung that responds |
|---|---|
| OpenAI | the latest top GPT model, on any account the user is signed in to |
| Anthropic | the latest Claude Opus, on any account the user is signed in to, then the same Opus through another harness such as Cursor |
| Third lab | the latest Gemini Pro, then the latest Grok, then another lab's top model |

- Run every seat at `high` effort. At xhigh or max, reviewers keep finding nits forever.
- A seat that fails twice moves down its ladder. A seat that hits a usage limit tries the next account or plan before it counts as a failure.
- A new rung reviews the current fingerprint as a fresh seat.
- Use no timers or status polls. At your first wake past a seat's 60th minute, cancel it and count a failure. If the only seats left are still out, end your turn and say so (in ship-ready, the one blocker message); their notice or the user's next message wakes you.
- A member the user named for this run has no ladder: if it is unavailable or fails twice, the outcome is BLOCKED.
- When fewer than three labs remain, finish the round as a report. Its outcome is BLOCKED, unless the user waives the missing lab.
- How to reach each seat, in order of preference: [references/routes.md](references/routes.md).

## 3. Run a round

Start one review per seat. Run seats in parallel unless your setup caps concurrent helpers; then start the next seat when one returns. In T3 Code, use one `delegate_task` per seat:

- mode `async` and role `review`
- `runtimeMode: "full-access"` unless the user asks for supervised seats: a seat on another machine does not inherit your mode and otherwise stalls on approval prompts
- a new `clientRequestId` each round
- `isolation: "worktree"` when the artifact is in git, so seats can build and test without touching each other's files

Send each seat the brief.

- Seats are read-only, start no subagents, and may run, build, render and test.
- Do not edit the artifact until every seat has returned. As each result arrives, reproduce its findings. Fix nothing yet.
- A timeout, an error or no reply is never a pass.
- Each seat's reply starts with the fingerprint it read. Discard a reply whose fingerprint differs from the one you sent, rerun that seat, and count a failure.

## 4. Triage every finding

For each finding:

1. **Check its proof.**
   - Code and facts: re-run the command or re-check the source.
   - Prose and design: confirm the quoted text breaks the rule it names (taste, brand or brief).
   - If it does not hold up, record `not reproduced` and drop it.
2. **Re-rate its severity** against the brief. An issue that predates the work and sits outside the intent is a **nit**, whatever label it came with. A problem the work introduces or exposes keeps its severity, whatever the scope. A proven blocker from one lab still blocks.
3. **Merge duplicates by root cause.** When labs agree on a root cause, the signal is strong.
4. **Act on it:**
   - Agree: make the smallest fix. Delete or narrow before you add.
   - Disagree: answer with evidence.
   - Nit: decline it in one line and list it as a follow-up. A declined nit leaves the fingerprint unchanged.
   - Your own concern: log it as a finding and treat it like any other.

Log every finding in the **ledger**: id, seat, severity, outcome and evidence. Format: [references/receipt.md](references/receipt.md).

Settle reversible choices yourself and log each one for the receipt. Ask the user only for what only they can give: a secret, a spend, new access or a change of goal.

After the fixes, re-run the checks, commit, and measure the size again. Growth is the size now minus the baseline. The **scope** guard applies when growth is more than the larger of 25% of the baseline or 40 lines (150 words for prose):

- Cut the growth, or justify each added part in the ledger. A fix or test for a proven blocker or should-fix counts as justified.
- If the growth is past the intent, that is a TAP OUT.
- Do not agree to a finding just to end the loop. That is a failed run.

## 5. Next round, or stop

Run the next round when budget remains and any of these is true:

- a blocker or should-fix is still open
- the fingerprint changed after the last scores
- a seat below the bar, or with no score, has not yet seen the triage outcomes in the ledger

Every round, every seat scores the current fingerprint. From round 2 on, add the ledger and what changed to the brief. Seats hunt in the changed parts, in the open ids, and in anything those changes touch.

Stop with exactly one outcome:

- **PASS** or **SINGLE-SEAT PASS**: as defined above. A pass wins over the tap-out rules below, but never over the scope guard.
- **TAP OUT**: no pass, and one of these is true:
  - the same finding is still disputed after two replies
  - two rounds in a row did not raise the lowest score
  - the budget is spent: 3 rounds, or 5 when the user asks or the work is high-risk (public, paid, or reaching many users)

  Spent budget is never approval.
- **BLOCKED**: fewer than three labs are reachable without a waiver, a usage limit cannot be routed around, or access is missing.

When a seat scores below the bar or says CHANGES but lists only nits, ask it once which should-fix costs the points. If it names none, record the score and tap out with that as the dispute.

## 6. Hand back

A pass covers one fingerprint. Any later change to the artifact needs a **confirm round**: a full round, every seat, on the new fingerprint. It uses the run's remaining budget. With none left, the outcome is TAP OUT; never restart the count. The receipt, the ledger and a PR description are not the artifact, so changing them needs no confirm round.

Stop one step before any send, publish, schedule, merge, deploy or charge. That step stays the user's tap.

Return the receipt from [references/receipt.md](references/receipt.md). It includes:

- the outcome, the bar and the version
- the scores, seat by round
- what was fixed and what was declined
- the size before and after
- where the proof is
- the exact go action

On a tap out, add the best version, each open dispute in 2-3 lines per side, and one next step. When the work ends in a PR, put the receipt's `## Council review` section in the PR description.
