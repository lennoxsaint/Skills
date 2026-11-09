# Goal

Goal turns an existing plan, specification, or task list into one bounded execution contract.

Use it when a job is too important for a vague "keep going until it works" prompt. The skill keeps the strategy intact, defines proof and stop conditions, and makes steering survive a long Codex run.

## Install

```bash
git clone --depth 1 https://github.com/lennoxsaint/Skills.git
python3 Skills/scripts/skills.py install goal --host codex
```

Use `--host claude` for Claude Code, or `--host both` for both. Start a new session if the skill does not appear immediately.

## Use with Codex

Give `$goal` a real plan:

```text
Use $goal to turn this plan into a durable Codex goal packet:

1. Replace the old billing screen.
2. Keep current prices and permissions.
3. Prove desktop and mobile checkout.
4. Do not deploy without approval.
```

The skill creates two local files inside the workspace:

- `goal.md`: the owner-editable contract
- `progress.md`: the agent-maintained checkpoint record

It then returns a paste-ready `/goal` launcher. Creating the files does not start Goal Mode by itself.

## Use with Claude

Ask for a Claude goal prompt and provide the plan. Goal returns one paste-ready `/goal` prompt of no more than 4,000 characters. It does not create a Codex packet in Claude mode.

## Why two files

The goal contract should stay stable while the work runs. Progress changes often. Keeping them separate means the owner can steer the outcome without turning the contract into a running diary.

The active thread remains the highest authority. Codex re-reads the goal before checkpoints and live actions, records the goal hash it used, and changes strategy after repeated failures instead of looping forever.

## Safety

Goal does not turn a broad objective into hidden permission. Sending, publishing, deleting, charging, deploying, merging, or writing production data still requires exact authorization in the source plan.

Goal packets are local runtime artifacts. The skill does not stage or commit them unless the user explicitly asks.

## Changelog

**1.1.0** (10 Nov 2026) - two additions to the skill text. First, an entry guard: when a goal is already running and the host asks the agent to continue it, the agent carries on with the next authorized step. It does not rebuild the packet, return the launcher again or ask for the plan again. Second, a route: when the goal is a quality bar that real data can measure, the skill points to [Hill Climb](hill-climb.md) when it is installed. The packet format, the templates and the helper scripts are unchanged.

**1.0.0** (20 Sep 2026) - first public release.
