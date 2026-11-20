# Council

Council is for work you want three different AI labs to sign off on before it goes out.

Your agent sends the exact same version to one reviewer from each of three labs, for example GPT, Claude and Gemini. Each reviewer scores it out of 10 twice: is it right, and would you ship it as is. Your agent checks every finding, fixes what is proven with the smallest change, and sends the new version back. It stops when every reviewer clears your bar, when the loop stops making progress, or when it is blocked. Then it hands you a one-screen receipt and waits for your go.

## When it runs

It runs when you ask for it:

- "council this PR"
- "council 9.5 on the pricing page"
- "get three different models to review this until they all agree"
- "council: would our power users be happy with this?"
- "ask a council of models whether we should raise prices"

For one reviewer against a 100-point rubric, use [Adversarial Review](adversarial-review.md) instead. To take a whole task to ready-to-go with council as the last gate, use [Ship-ready](ship-ready.md).

## How a round works

1. **Finish first.** Your agent fixes known issues and runs the checks before round 1. The council reviews its best version.
2. **Freeze the brief.** Intent, what is out of scope, the audience, the checks already run, and the exact version. The bar is left out so it doesn't anchor the scores.
3. **Fingerprint the version.** A git commit SHA, or the SHA256 of each file. Every reviewer replies with the fingerprint it read. A reply about the wrong version is thrown away.
4. **Seat three labs.** The latest top model from each, at high effort. A seat that fails twice moves down its ladder to another model from the same lab, or another lab for the third seat.
5. **Check every finding.** Each one needs proof: a command and its output, or the quoted text and the rule it breaks. Unproven findings are dropped. Old problems outside the task are nits. Problems the work introduced keep their severity.
6. **Fix the smallest thing**, re-run the checks, and measure the size. If the change grew past 25% (or 40 lines, or 150 words), each addition must be justified or cut.
7. **Go again** while anything real is open, then stop with one outcome.

## The outcomes

| Outcome | What it means |
|---|---|
| PASS | Three labs, every seat at or above the bar on both scores, every seat says SHIP, nothing real left open |
| SINGLE-SEAT PASS | You asked for one reviewer, and it passed. Never reported as a council pass. |
| TAP OUT | No pass, and the loop stalled: the same dispute twice, two rounds with no rise in the lowest score, or the round budget spent (3, or 5 for public or paid work) |
| BLOCKED | Fewer than three labs reachable and you did not waive one, a usage limit it could not route around, or missing access |

A pass covers one exact version. Any later change to the work needs a confirm round: every seat scores the new version, out of the same round budget.

## The second score

The second score asks: would you ship this exactly as it is? Reviewers judge it from taste and brand files you name. You can also set `COUNCIL_TASTE_FILE` to a file of your preferences, for example `export COUNCIL_TASTE_FILE=~/notes/taste.md`. With no such file, reviewers judge it from the intent and audience in the brief.

You can swap the question too: "council: would our designer be happy with this?"

## What it will not do

- It will not send, publish, schedule, merge, deploy or charge. It stops one step before, and that step is yours.
- It will not call spent budget approval. A tap out says so, with each open dispute in a few lines per side.
- It will not count two models from the same lab as two labs. A same-lab review is labelled as one.
- It will not use a paid API route such as OpenRouter unless you approve the spend for that run.

## Install

```bash
git clone --depth 1 https://github.com/lennoxsaint/Skills.git
python3 Skills/scripts/skills.py install council --host claude
```

Use `--host codex` for Codex, or `--host both` for both. Start a new session if the skill does not show up right away.

Then try:

```text
Council 9 on this PR: have three labs review it and loop until they would all ship it.
```

## What you need

Reviewers from three AI labs that your agent can reach. The easiest setup is T3 Code, whose `delegate_task` runs each seat in its own lab's harness. Without it, the lab CLIs you are signed in to: Codex for GPT, Claude Code for Claude, and Gemini CLI or Cursor for the third lab. With only one lab, you get a single-seat review.

## Your data

The work and its brief go to each reviewer's provider, on your own sign-ins. Decide what reviewers may read before you start. A paid outside route gets redacted content only.

## What it costs

Each round is one call per seat on your own accounts. A round budget caps it at 3 rounds, or 5 for public or paid work.

## Files in the skill

| File | What it is |
|---|---|
| `SKILL.md` | The loop, the pass rule, triage, the stop rules |
| `references/brief.md` | The brief every seat gets, and the reply shape |
| `references/receipt.md` | The ledger, the receipt and the PR section |
| `references/routes.md` | How to reach each seat: T3 Code, lab CLIs, subagents, OpenRouter |
| `references/decide.md` | Decide mode, for a question with no artifact yet |

A synthetic example lives in [`examples/council/`](../examples/council/sample-receipt.md). The test evidence is in the [evaluation](../evaluations/council.md).

## Prior art

Theo Browne's council video (16 Nov 2026) and his [tstack](https://github.com/t3dotgg/tstack) (MIT) came first. The run numbers quoted in `SKILL.md`, about 7.5 rising to 9 in two or three rounds, and the uncapped loop that ran 50+ rounds, come from that video.

## Changelog

**1.0.1** (21 Nov 2026) - seats start with `runtimeMode: "full-access"` unless the user asks for supervised seats. A seat launched on a linked machine did not inherit the caller's mode and stalled on approval prompts.

**1.0.0** (16 Nov 2026) - first public release. This is the council I run, with my private paths, tools and taste files replaced by general ones. Its text went through five rounds of its own council before release.
