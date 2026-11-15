# Strategy Prompt

Strategy Prompt is for a decision you keep going back and forth on.

You give it the question and the options. It argues the best case for each one, scores them all on the same criteria, picks one, then attacks its own pick before it gives you a final answer.

## When it runs

It runs when you ask for it:

- "strategy prompt this"
- "steelman both sides"
- "score the options"
- "compare these strategic choices"
- "give me a rigorous recommendation"

It is for business, strategy and research decisions with real options. It is not for a quick opinion or a pros and cons list.

## How it works

1. **Read your context first.** Your notes, numbers and past decisions, when the agent can reach them. It says what it found and what it could not reach.
2. **Name the options.** If you only give one, it adds the strongest real alternatives.
3. **Steelman each one.** The best honest case, even for the option it will not pick.
4. **Pick 5 to 8 criteria** that fit your goal, and weight them to exactly 100%.
5. **Score every option** from 1 to 10 on every criterion. 10 is always best for you, so low risk scores high.
6. **Show the matrix and the math.**
7. **Give a first recommendation** from the matrix.
8. **Double-check it.** Bias, edge cases, missing criteria, the math, and "what would make me wrong about this?"
9. **Give the final recommendation.** A clear answer, why it fits your goals, how sure it is, what it assumes and what to do next.

The final answer is allowed to differ from the first one. When the double-check changes a weight or a score, you see the new totals next to the old ones and what changed its mind.

## What you get back

Six sections, always in this order:

| Section | What is in it |
|---|---|
| Options | What is being compared, and what context was found |
| Steelman | The best case for each option |
| Scoring Algorithm | Criteria, weights, scores and totals |
| Initial Recommendation | What the matrix says |
| Double-Check | Bias, gaps, math check, what would make it wrong |
| Final Recommendation | The answer, confidence, assumptions, next steps |

## How to read the numbers

The scores are judgment, not measurement. The skill has to say so when a number is only a direction. The matrix makes the reasoning easy to argue with. It does not make the answer true.

For a high-stakes call, the skill tells you to get a second opinion from a different model and names the scores most open to dispute.

## Install

```bash
git clone --depth 1 https://github.com/lennoxsaint/Skills.git
python3 Skills/scripts/skills.py install strategy-prompt --host claude
```

Use `--host codex` for Codex, or `--host both` for both. Start a new session if the skill does not show up right away.

Then try:

```text
Use the strategy prompt: steelman both options, score them, and tell me which one to pick.
```

## What you need

Nothing to install. A tool that can read your own notes helps, and so does web search when current facts matter. The skill works without either and says what it could not reach.

## Files in the skill

| File | What it is |
|---|---|
| `SKILL.md` | The ten steps, the rules and the six output headings |

A synthetic example lives in [`examples/strategy-prompt/`](../examples/strategy-prompt/sample-question.md). The test evidence is in the [evaluation](../evaluations/strategy-prompt.md).

## Changelog

**1.0.0** (10 Nov 2026) - first public release. This is the prompt I use for my own business decisions. Two private tool names were replaced with general steps ("read the user's own context", "get a second opinion from a different model"). Three lines were made clearer after a test with an agent that had never seen the skill: which way the scores run, that the final answer may differ from the first, and where the context note goes.
