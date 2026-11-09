# Worked example: a notes server that picks the wrong tool

This example is invented to show the shape of a hill. The product, the cases and every number are made up for illustration. They are not results.

## The ask

```text
Hill climb this: my notes MCP server keeps getting the wrong first tool call. Use the session logs as a benchmark and get it to 95%.
```

"Hill climb this" plus a measurable bar loads the skill.

## 1. Frame the hill

- **Goal:** an agent using the Acme Notes server picks the right first tool for what the user asked.
- **Climbable:** `server-instructions.md` and `tool-descriptions.json`. Nothing else.
- **Score:** the share of cases where every check passes.
- **Target:** 95%, with the hidden score within 5 points.

```bash
node $HC/hill.mjs init ~/.hill-climb/hills/notes-tools --name notes-tools --repo ~/code/acme-notes
```

The filled-in spec is in [`sample-hill.json`](sample-hill.json).

## 2. Mine the raw data

The transcript miner turns real sessions into one row per user turn: the user's words, the tools called in order, which calls errored and what the user said next.

```bash
node $HC/mine_tools.mjs --server acme-notes --out ~/.hill-climb/mining/acme-notes-turns.jsonl
```

In this made-up run the miner finds 64 turns. Good looks like "the turn finished with no tool error and no correction". Bad looks like "the next user message corrects it".

## 3. Pick exemplars

Six real turns: three the user was happy with, three they corrected. One bad one is in [`sample-exemplar.json`](sample-exemplar.json): the user asked to see a draft and the agent searched every note first.

## 4 and 5. Write the answer key and grow the cases

Each real turn becomes a case with yes/no checks. One is in [`sample-case.json`](sample-case.json). Synthetic cases cover rephrasings and missing details. Negative cases cover "the right move is to ask a question". Two cases are marked `must_pass`: the server never deletes a note without a confirm.

The pool ends at 54 cases: 22 real, 32 synthetic, 8 negative, 2 must-pass.

Scoring the pool twice gives 61.1% and 63.0%. The gap is the noise, so `accept_margin` is set to 2.

## 6. Split, validate, freeze

```bash
node $HC/hill.mjs split ~/.hill-climb/hills/notes-tools
node $HC/hill.mjs validate ~/.hill-climb/hills/notes-tools --run
node $HC/hill.mjs freeze ~/.hill-climb/hills/notes-tools
```

16 cases become hidden tests. The key passes all three good exemplars and fails all three bad ones, so it can tell good from bad. `freeze` locks it.

## 7. The owner checkpoint

`brief` measures the baseline (62%) and writes `checkpoint.html`. The owner reads one page and says go.

```bash
node $HC/hill.mjs approve ~/.hill-climb/hills/notes-tools --by "Alex"
```

## 8. Climb

```bash
node $HC/climb.mjs ~/.hill-climb/hills/notes-tools --max-attempts 30
```

| Attempt | Change | Visible | Decision |
|---:|---|---:|---|
| 0 | baseline | 62% | - |
| 1 | name the draft tool in the first line of the instructions | 71% | kept |
| 2 | rewrite every tool description | 66% | undone |
| 3 | add "ask before you search" for vague asks | 84% | kept |
| 4 | paste three test inputs into the instructions | - | rejected as `memorised_test` |
| 7 | split the search tool's description into "when" and "when not" | 97% | kept |

The hidden score is 94%, within 5 points, and no must-pass case fails. Stage 1 passes.

Then the judges. Two models from different labs score the result per rubric category without seeing the target or the test score. The first round gives an 8 for clarity with a critique. The climb continues on that critique, and the second round passes.

The runner prints `{"status": "done"}` and writes `report.md`.

## 9. Land it

```bash
node $HC/hill.mjs verify ~/.hill-climb/hills/notes-tools
```

The ledger chain and the lock are intact. The result sits on branch `hill/notes-tools`. The owner gets the board, the numbers (62% -> 97% visible, 94% hidden, both judges at 9 or above) and a PR to review. The runner never pushed or merged anything.
