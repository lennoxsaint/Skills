# Strategy Prompt

strategy-prompt is for a decision you keep going back and forth on.

you give it the question and the options. it argues the best case for each one, scores them all on the same criteria, picks one, then attacks its own pick before it gives you a final answer.

## when it runs

it runs when you ask for it:

- "strategy prompt this"
- "steelman both sides"
- "score the options"
- "compare these strategic choices"
- "give me a rigorous recommendation"

it is for business, strategy and research decisions with real options. it is not for a quick opinion or a pros and cons list.

## how it works

1. **read your context first.** your notes, numbers and past decisions, when the agent can reach them. it says what it found and what it could not reach.
2. **name the options.** if you only give one, it adds the strongest real alternatives.
3. **steelman each one.** the best honest case, even for the option it will not pick.
4. **pick 5 to 8 criteria** that fit your goal, and weight them to exactly 100%.
5. **score every option** from 1 to 10 on every criterion. 10 is always best for you, so low risk scores high.
6. **show the matrix and the math.**
7. **give a first recommendation** from the matrix.
8. **double-check it.** bias, edge cases, missing criteria, the math, and "what would make me wrong about this?"
9. **give the final recommendation.** a clear answer, why it fits your goals, how sure it is, what it assumes and what to do next.

the final answer is allowed to differ from the first one. when the double-check changes a weight or a score, you see the new totals next to the old ones and what changed its mind.

## what you get back

six sections, always in this order:

| section | what is in it |
|---|---|
| Options | what is being compared, and what context was found |
| Steelman | the best case for each option |
| Scoring Algorithm | criteria, weights, scores and totals |
| Initial Recommendation | what the matrix says |
| Double-Check | bias, gaps, math check, what would make it wrong |
| Final Recommendation | the answer, confidence, assumptions, next steps |

## read the numbers the right way

the scores are judgment, not measurement. the skill has to say so when a number is only a direction. the matrix makes the reasoning easy to argue with. it does not make the answer true.

for a high-stakes call, the skill tells you to get a second opinion from a different model and names the scores most open to dispute.

## install

```bash
git clone --depth 1 https://github.com/lennoxsaint/Skills.git
python3 Skills/scripts/skills.py install strategy-prompt --host claude
```

use `--host codex` for Codex, or `--host both` for both. start a new session if the skill does not show up right away.

then try:

```text
Use the strategy prompt: steelman both options, score them, and tell me which one to pick.
```

## what you need

nothing to install. a tool that can read your own notes helps, and so does web search when current facts matter. the skill works without either and says what it could not reach.

## files in the skill

| file | what it is |
|---|---|
| `SKILL.md` | the ten steps, the rules and the six output headings |

a synthetic example lives in [`examples/strategy-prompt/`](../examples/strategy-prompt/sample-question.md). the test evidence is in the [evaluation](../evaluations/strategy-prompt.md).

## changelog

**1.0.0** (10 Nov 2026) - first public release. this is the prompt i use for my own business decisions. two private tool names were replaced with general steps ("read the user's own context", "get a second opinion from a different model"). three lines were made clearer after a test with an agent that had never seen the skill: which way the scores run, that the final answer may differ from the first, and where the context note goes.
