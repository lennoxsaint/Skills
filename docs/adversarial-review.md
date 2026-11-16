# Adversarial Review

Adversarial Review is for work you want a second model to try to break.

Your agent freezes the draft and a rubric, sends them to an independent reviewer in a fresh session, checks every finding against the sources, fixes what holds up, and sends the whole new version back. It keeps going until the bar is met or the budget runs out. Then it tells you which one happened.

## When it runs

It runs when you ask for it:

- "adversarial review this plan"
- "red-team this"
- "get another model to tear this apart"
- "iterate until you and the reviewer agree"

It reviews the thing you asked about: an answer, a plan, a workflow, a skill, a piece of code. It does not quietly turn a review into building the thing.

See also [Council](council.md): the same idea with reviewers from three AI labs at once, each scoring out of 10.

## How a review works

1. **Freeze the contract.** A short brief, the exact draft, the source facts, a rubric that adds up to 100, and when to stop. The default bar is 90 out of 100 and the default budget is three rounds.
2. **Snapshot and hash.** Each version gets a number and a SHA-256, so every verdict is tied to an exact version.
3. **Review in a fresh context.** The reviewer sees the brief, the draft and the evidence. It is not given the author's opinion, the old scores or the answer you hope for.
4. **Check each finding.** Supported ones are accepted. Wrong ones are rejected with evidence. Ones nobody can check are marked unresolved.
5. **Fix the smallest part** that solves the biggest supported problem.
6. **Send the whole new version** to a new reviewer session, with the same rubric.
7. **Stop and report.** The version and hash, who reviewed, the score history, what changed, what is still open, and which checks really ran.

## What keeps it honest

- **The reviewer is labelled.** A different model family is `different_family`. A new session of the same model is `same_family_fresh_context`. The agent has to read the real model name from the tool's own output, not from the name it asked for.
- **A named model is not swapped.** If you ask for a reviewer that is not available, the review stops. It does not pick another one for you.
- **The rubric can't move.** Weights, bar and baseline are set before round one and stay put.
- **A retry is not a second chance.** The same draft is never sent again just to fish for a higher score.
- **Every round is kept.** Prompt, raw reply and parsed verdict are saved, and a scored round is never overwritten.
- **A score is not a pass.** The bar must be met and every critical or high finding must be fixed or withdrawn with evidence.
- **A pass is not proof.** Agreement says the draft was reviewed. It does not say the plan works.

## Install

```bash
git clone --depth 1 https://github.com/lennoxsaint/Skills.git
python3 Skills/scripts/skills.py install adversarial-review --host claude
```

Use `--host codex` for Codex, or `--host both` for both. Start a new session if the skill does not show up right away.

Then try:

```text
Run an adversarial review of this plan with a 90/100 bar and an independent reviewer.
```

## What you need

A second reviewer your agent can reach. The strongest setup is another lab's command-line tool. That is Codex if you work in Claude Code, and Claude Code if you work in Codex. A fresh session of the same model also works and is labelled as the weaker kind of independence.

## Your data

The draft and its evidence go to the reviewer's provider. The skill tells the agent to send only what the review needs and to leave out secrets and unrelated private material. Decide what the reviewer may read before you start.

## What it costs

Each round is one reviewer call on your own account. The skill uses the sign-in you already have. It will not buy capacity, switch accounts or turn on a paid fallback.

## Files in the skill

| File | What it is |
|---|---|
| `SKILL.md` | The review contract, the loop and the stop rules |
| `references/reviewer-contract.md` | What the reviewer is given, and the receipt saved for each round |

A synthetic example lives in [`examples/adversarial-review/`](../examples/adversarial-review/sample-plan.md). The test evidence is in the [evaluation](../evaluations/adversarial-review.md).

## Changelog

**1.0.0** (10 Nov 2026) - first public release. This is the review method I run between models, with notes about my own machines and one product-specific reference file left out. Three lines were made clearer after a test with an agent that had never seen the skill: write a rubric when none is given, where to read the real model name, and what to record when no model was named.
