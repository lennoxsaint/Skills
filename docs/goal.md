# Goal

Goal turns an existing plan, specification, or task list into one bounded execution contract.

Use it when a job is too important for a vague "keep going until it works" prompt. The skill keeps the strategy intact, defines proof and stop conditions, and makes steering survive a long Codex run.

## Install

```bash
git clone https://github.com/lennoxsaint/Skills.git
cd Skills
python3 scripts/skills.py install goal
```

Restart Codex if the skill does not appear immediately.

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
