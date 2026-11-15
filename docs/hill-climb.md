# Hill Climb

Hill Climb is for the long jobs where "looks good to me" is not enough.

You give it real data. It turns that data into a locked set of yes/no tests. Then it sends fresh agent sessions at the work, one small change at a time, and keeps only the changes that raise the score. It stops when the number hits the target and two outside judges say they would ship it.

## The idea

A **hill** is one goal with an **answer key**. The answer key is a set of test cases built from things that really happened, such as logs, transcripts, posts you rewrote and bugs people reported.

The agent that does the climbing never sees the hidden tests. It can't grade its own work. It can't edit the tests. Every attempt is scored by a script, and every result is written to disk.

Most of the work is building a good answer key. The climb itself is a script.

## When it runs

It runs when you ask for it:

- "hill climb this"
- "build an eval and climb it"
- "make the agent hit 90%"
- "use the logs as a benchmark"
- "keep going until it passes"

It is not for quick polish of one draft: use [Loop](loop.md) for that. If you can't say what the score measures, you are not ready for a hill yet.

## How a climb works

```mermaid
flowchart LR
  A[Frame the hill] --> B[Mine real data]
  B --> C[Write the answer key]
  C --> D[Split, check, freeze]
  D --> E[You approve once]
  E --> F[Climb]
  F -->|Score up| G[Keep the change]
  F -->|Score flat or down| H[Undo it]
  G --> F
  H --> F
  F --> I[Two outside judges]
  I -->|Critiques| F
  I --> J[Done]
```

**1. Frame the hill.** One sentence each for the goal, the files the agent may change, what the score measures, and a target number.

**2. Mine real data.** At least 20 real examples, each with where it came from. The skill ships a miner that turns Claude Code and Codex transcripts into one row per user turn.

**3. Pick examples of good and bad.** 3 to 10 real outputs you already know are good or bad. These test the tests.

**4. Write the answer key.** Yes/no checks only. Code checks first (exact value, regex, length, a command). A yes/no model question only for what code can't see. No 1-10 scores inside a test.

**5. Grow the cases.** Turn each real example into a case, then add more around the edges until you have about 50. Some cases must never fail. Some are "the right move is to do nothing".

**6. Split, check, freeze.** About 30% of the cases become hidden tests. The key has to pass your good examples and fail your bad ones at least 80% of the time. Then it is hashed and locked.

**7. You approve once.** The skill builds a one-page checkpoint: the goal, today's score, the target, sample tests, the stop rules. This is the only stop. After your yes, the climb is hands-off.

**8. Climb.** Each attempt is a new agent session. It sees the goal, the score, the failing visible tests and notes from past attempts. It makes one change and stops. The runner scores it, then keeps it as a commit or undoes it.

**9. Land it.** The result sits on its own git branch. You get the board, the numbers and a PR or a clear next move.

## How "done" is decided

Two stages. Both have to pass.

| Stage | What has to be true |
|---|---|
| Tests | The visible score reaches the target, the hidden score is within 5 points of it, and no must-pass case fails |
| Judges | Two models from different labs score the result per category, 1 to 10. Every judge has to give the bar (9 by default) in every category and say it would ship |

The judges are blind. They never see the target, the bar or the test score. For visual work they score screenshots of your work next to the best products you picked, shuffled under letters.

If the climb stops for another reason, it says so: `stuck`, `deadline`, `max_attempts`, `budget`. It never calls a miss a win.

## What keeps it honest

- **The agent can't see the hidden tests.** Every climber, test and judge runs in the machine's sandbox, with the hill folder hidden.
- **The agent can't edit the tests.** The answer key is hashed. If a hash changes mid-run, the climb stops as `tampered`.
- **Pasting test text into the work is rejected.** A change that copies a test's input is thrown out.
- **Only the allowed files change.** Any other changed file rejects the attempt.
- **The log can't be quietly rewritten.** Every entry carries the hash of the one before it.
- **It never ships.** The runner does not push, merge, publish, send or deploy. Landing the result is your call.
- **A killed run loses nothing.** Start the same command again and it picks up where it stopped.

## Install

For Claude Code:

```bash
git clone --depth 1 https://github.com/lennoxsaint/Skills.git
python3 Skills/scripts/skills.py install hill-climb --host claude
```

For Codex:

```bash
git clone --depth 1 https://github.com/lennoxsaint/Skills.git
python3 Skills/scripts/skills.py install hill-climb --host codex
```

Use `--host both` for both. Start a new session if the skill does not show up right away.

Then try:

```text
Hill climb this: build an answer key from my real logs, then climb until 90% of the cases pass.
```

Check that the runner works on your machine (no model calls, no cost, about 10 minutes). Use the path the installer printed:

```bash
node ~/.claude/skills/hill-climb/scripts/selftest.mjs   # Claude Code
node ~/.codex/skills/hill-climb/scripts/selftest.mjs    # Codex
```

## What you need

- Node 18 or newer and git. No packages to install.
- `zstd`, only if you mine Codex sessions that are stored compressed (`.jsonl.zst`). Without it the miner skips those files and tells you how many.
- macOS, for `sandbox-exec`. On Linux the runner uses `bwrap`, but that path is untested.
- Claude Code or Codex on the command line. Climbers and judges are fresh `claude -p` or `codex exec` sessions.
- Two labs for the judge stage. The default is one Codex judge and one Claude judge. Set `council` to `[]` in `hill.json` to skip the judges while you learn the tool. Then the tests alone decide `done`, and the stop reason says `no council configured`.

## What it costs

A climb is many agent sessions. Each attempt is one climber session plus scoring, and the judge stage adds two or more judge calls per round. Set `stop.max_attempts`, `stop.deadline` or `stop.budget_usd` before you start.

The dollar cap only counts what the tools report. Claude reports its cost. Codex runs are counted as "unknown cost", never as $0.

## Your data

The judges are outside models. The work, the diff and the test results go to each judge's provider. Decide what they may read before you climb, and keep secrets out of every case and example.

Everything else stays on your disk, in `~/.hill-climb/` by default.

## Files in the skill

| File | What it is |
|---|---|
| `SKILL.md` | The nine steps |
| `references/answer-key.md` | How to mine data and write checks |
| `references/hill-json.md` | Every setting in `hill.json` |
| `references/safety.md` | The sandbox, git safety and known limits |
| `scripts/hill.mjs` | Set up, score, freeze, brief, approve, verify |
| `scripts/climb.mjs` | The runner |
| `scripts/selftest.mjs` | Proves the runner with fake agents |

A synthetic example lives in [`examples/hill-climb/`](../examples/hill-climb/worked-example.md). The test evidence is in the [evaluation](../evaluations/hill-climb.md).

## Changelog

**1.0.1** (10 Nov 2026) - one line changed. The description now sends quick polish of one draft to [Loop](loop.md), which is public as of today. The method and the scripts are the same as 1.0.0.

**1.0.0** (10 Nov 2026) - first public release. This is the version I run, as of 4 Nov 2026, with the blind judge stage. Private paths and product-specific notes were replaced with general ones. The method and the scripts are the same.
