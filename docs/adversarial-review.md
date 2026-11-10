# Adversarial Review

adversarial-review is for work you want a second model to try to break.

your agent freezes the draft and a rubric, sends them to an independent reviewer in a fresh session, checks every finding against the sources, fixes what holds up, and sends the whole new version back. it keeps going until the bar is met or the budget runs out. then it tells you which one happened.

## when it runs

it runs when you ask for it:

- "adversarial review this plan"
- "red-team this"
- "get another model to tear this apart"
- "iterate until you and the reviewer agree"

it reviews the thing you asked about: an answer, a plan, a workflow, a skill, a piece of code. it does not quietly turn a review into building the thing.

## how a review works

1. **freeze the contract.** a short brief, the exact draft, the source facts, a rubric that adds up to 100, and when to stop. the default bar is 90 out of 100 and the default budget is three rounds.
2. **snapshot and hash.** each version gets a number and a SHA-256, so every verdict is tied to an exact version.
3. **review in a fresh context.** the reviewer sees the brief, the draft and the evidence. it is not given the author's opinion, the old scores or the answer you hope for.
4. **check each finding.** supported ones are accepted. wrong ones are rejected with evidence. ones nobody can check are marked unresolved.
5. **fix the smallest part** that solves the biggest supported problem.
6. **send the whole new version** to a new reviewer session, with the same rubric.
7. **stop and report.** the version and hash, who reviewed, the score history, what changed, what is still open, and which checks really ran.

## what keeps it honest

- **the reviewer is labelled.** a different model family is `different_family`. a new session of the same model is `same_family_fresh_context`. the agent has to read the real model name from the tool's own output, not from the name it asked for.
- **a named model is not swapped.** if you ask for a reviewer that is not available, the review stops. it does not pick another one for you.
- **the rubric can't move.** weights, bar and baseline are set before round one and stay put.
- **a retry is not a second chance.** the same draft is never sent again just to fish for a higher score.
- **every round is kept.** prompt, raw reply and parsed verdict are saved, and a scored round is never overwritten.
- **a score is not a pass.** the bar must be met and every critical or high finding must be fixed or withdrawn with evidence.
- **a pass is not proof.** agreement says the draft was reviewed. it does not say the plan works.

## install

```bash
git clone --depth 1 https://github.com/lennoxsaint/Skills.git
python3 Skills/scripts/skills.py install adversarial-review --host claude
```

use `--host codex` for Codex, or `--host both` for both. start a new session if the skill does not show up right away.

then try:

```text
Run an adversarial review of this plan with a 90/100 bar and an independent reviewer.
```

## what you need

a second reviewer your agent can reach. the strongest setup is another lab's command-line tool: Codex if you work in Claude Code, Claude Code if you work in Codex. a fresh session of the same model also works and is labelled as the weaker kind of independence.

## your data

the draft and its evidence go to the reviewer's provider. the skill tells the agent to send only what the review needs and to leave out secrets and unrelated private material. decide what the reviewer may read before you start.

## what it costs

each round is one reviewer call on your own account. the skill uses the sign-in you already have. it will not buy capacity, switch accounts or turn on a paid fallback.

## files in the skill

| file | what it is |
|---|---|
| `SKILL.md` | the review contract, the loop and the stop rules |
| `references/reviewer-contract.md` | what the reviewer is given, and the receipt saved for each round |

a synthetic example lives in [`examples/adversarial-review/`](../examples/adversarial-review/sample-plan.md). the test evidence is in the [evaluation](../evaluations/adversarial-review.md).

## changelog

**1.0.0** (10 Nov 2026) - first public release. this is the review method i run between models, with notes about my own machines and one product-specific reference file left out. three lines were made clearer after a test with an agent that had never seen the skill: write a rubric when none is given, where to read the real model name, and what to record when no model was named.
